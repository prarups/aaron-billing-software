from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction, models
from django.utils import timezone
from django.db.models import Sum, Count, F, Subquery, OuterRef
from django.template.loader import get_template
from core.models import Product
from inventory.models import Inventory
from .models import Bill, BillItem
import json
import csv
from io import BytesIO
try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except ImportError:
    XHTML2PDF_AVAILABLE = False

@login_required
def pos_index(request):
    # Get products for the user's active branch
    if not request.user.active_branch:
        return render(request, 'pos/index.html', {'error': 'No active branch selected. Please log in again.'})
    
    inventory_items = Inventory.objects.filter(
        branch=request.user.active_branch, 
        stock_quantity__gt=0
    ).select_related('product')
    return render(request, 'pos/index.html', {'inventory': inventory_items})

@login_required
def get_product_by_barcode(request):
    barcode = request.GET.get('barcode')
    if not barcode:
        return JsonResponse({'error': 'No barcode provided'}, status=400)
    
    try:
        # Check if product exists and is in the user's active branch inventory
        inventory_item = Inventory.objects.get(
            product__barcode=barcode, 
            branch=request.user.active_branch,
            stock_quantity__gt=0
        )
        product = inventory_item.product
        return JsonResponse({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'stock': inventory_item.stock_quantity
        })
    except Inventory.DoesNotExist:
        return JsonResponse({'error': 'Product not found in this branch'}, status=404)

@login_required
@transaction.atomic
def process_bill(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            items = data.get('items', [])
            customer_name = data.get('customer_name', '')
            customer_phone = data.get('customer_phone', '')
            payment_method = data.get('payment_method', 'cash')
            
            if not items:
                return JsonResponse({'error': 'Cart is empty'}, status=400)
            
            with transaction.atomic():
                # Create Bill
                bill = Bill.objects.create(
                    branch=request.user.active_branch,
                    staff=request.user,
                    customer_name=customer_name,
                    customer_phone=customer_phone,
                    total_amount=0,  # Will update after items
                    payment_method=payment_method
                )
                
                total_amount = 0
                for item in items:
                    # select_for_update prevents race conditions on stock
                    product = get_object_or_404(Product, id=item['id'])
                    quantity = int(item['quantity'])
                    
                    inventory = Inventory.objects.select_for_update().get(
                        branch=request.user.active_branch, 
                        product=product
                    )
                    
                    if inventory.stock_quantity < quantity:
                        raise ValueError(f"Insufficient stock for {product.name}")
                    
                    inventory.stock_quantity -= quantity
                    inventory.save()
                    
                    bill_item = BillItem.objects.create(
                        bill=bill,
                        product=product,
                        quantity=quantity,
                        unit_price=product.price,
                    )
                    total_amount += bill_item.subtotal
                
                bill.total_amount = total_amount
                bill.save()
                
            return JsonResponse({'success': True, 'bill_id': bill.id})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'Invalid request'}, status=405)

@login_required
def bill_detail(request, bill_id):
    """Show a web-based bill receipt with download & WhatsApp buttons."""
    # Ensure user can only see bills from their active branch
    bill = get_object_or_404(Bill, id=bill_id)
    if not request.user.is_superuser and bill.branch != request.user.active_branch:
        return HttpResponse("Unauthorized to view this bill.", status=403)
        
    items = bill.items.select_related('product').all()
    
    # Build WhatsApp message text
    public_url = request.build_absolute_uri(f"/billing/share/{bill.share_id}/")
    wa_lines = [f"*Bill #{bill.id} - {bill.branch.name}*"]
    wa_lines.append(f"View/Download Bill: {public_url}")
    wa_text = "%0A".join(wa_lines)
    wa_link = f"https://wa.me/{bill.customer_phone}?text={wa_text}" if bill.customer_phone else None
    
    return render(request, 'billing/bill_detail.html', {
        'bill': bill,
        'items': items,
        'wa_link': wa_link,
        'public_url': public_url
    })

def public_bill_detail(request, share_id):
    """Publicly accessible bill view for customers (no login required)."""
    bill = get_object_or_404(Bill, share_id=share_id)
    items = bill.items.select_related('product').all()
    return render(request, 'billing/public_bill_detail.html', {
        'bill': bill,
        'items': items,
    })

def public_bill_pdf(request, share_id):
    """Publicly accessible PDF download for customers (no login required)."""
    bill = get_object_or_404(Bill, share_id=share_id)
    
    template = get_template('billing/bill_pdf.html')
    html = template.render({'bill': bill, 'request': request})
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Bill-{bill.id}.pdf"'
    
    buf = BytesIO()
    pisa.CreatePDF(html, dest=buf, link_callback=link_callback)
    
    response.write(buf.getvalue())
    return response

import os
from django.conf import settings
from django.contrib.staticfiles import finders

def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources on disk.
    """
    # use short variable names
    s_url = settings.STATIC_URL
    s_root = settings.STATIC_ROOT
    m_url = settings.MEDIA_URL
    m_root = settings.MEDIA_ROOT

    if uri.startswith(m_url):
        path = os.path.join(m_root, uri.replace(m_url, ""))
    elif uri.startswith(s_url):
        path = os.path.join(s_root, uri.replace(s_url, ""))
        if not os.path.exists(path):
            path = finders.find(uri.replace(s_url, ""))
    else:
        return uri

    # make sure that file exists
    if not os.path.isfile(path):
        return uri
    return path

@login_required
def bill_pdf(request, bill_id):
    """Generate and return a real PDF invoice using xhtml2pdf."""
    bill = get_object_or_404(Bill, id=bill_id)
    
    template = get_template('billing/bill_pdf.html')
    html = template.render({'bill': bill, 'request': request})
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Bill-{bill.id}.pdf"'
    
    buf = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buf, link_callback=link_callback)
    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)
    
    response.write(buf.getvalue())
    return response

@login_required
def staff_activity(request):
    date_str = request.GET.get('date', timezone.now().date().isoformat())
    try:
        target_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        target_date = timezone.now().date()
    
    # Filter bills for the logged-in staff at their active branch on the target date
    bills = Bill.objects.filter(
        staff=request.user,
        branch=request.user.active_branch,
        created_at__date=target_date
    ).order_by('-created_at').prefetch_related('items__product')
    
    # Aggregates
    stats = bills.aggregate(
        total_sales=Sum('total_amount'),
        transaction_count=Count('id')
    )
    
    # Items summary
    items_sold = BillItem.objects.filter(
        bill__in=bills
    ).values('product__name').annotate(total_qty=Sum('quantity')).order_by('-total_qty')

    context = {
        'bills': bills,
        'stats': stats,
        'items_sold': items_sold,
        'target_date': target_date.isoformat(),
        'today': timezone.now().date().isoformat(),
    }
    return render(request, 'billing/staff_activity.html', context)

@login_required
def owner_bill_list(request):
    """A comprehensive list of all bills for Owners and Managers."""
    if request.user.role == 'staff':
        return HttpResponse("Unauthorized", status=403)
    
    bills = Bill.objects.all().order_by('-created_at').select_related('branch', 'staff')
    
    # Filter by active branch if manager
    if request.user.role == 'manager':
        bills = bills.filter(branch=request.user.active_branch)
    
    # Filters from GET
    q = request.GET.get('q', '')
    branch_id = request.GET.get('branch')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    payment_method = request.GET.get('payment_method')
    
    # Handle search
    if q:
        from django.db.models import Q
        bills = bills.filter(
            Q(id__icontains=q) | 
            Q(customer_name__icontains=q) | 
            Q(customer_phone__icontains=q)
        )
    
    # Handle branch restriction
    if request.user.role == 'manager':
        branches = request.user.get_accessible_branches()
        # Ensure they can only filter branches they manage
        if branch_id and branch_id != 'None':
            if not branches.filter(id=branch_id).exists():
                branch_id = str(request.user.active_branch.id)
        else:
            # Default to active branch if no valid filter
            branch_id = str(request.user.active_branch.id)
    else:
        from core.models import Branch
        branches = Branch.objects.all()

    if branch_id and branch_id != 'None':
        bills = bills.filter(branch_id=branch_id)
    if start_date:
        bills = bills.filter(created_at__date__gte=start_date)
    if end_date:
        bills = bills.filter(created_at__date__lte=end_date)
    if payment_method:
        bills = bills.filter(payment_method=payment_method)
        
    # Stats for the filtered selection
    stats = bills.aggregate(
        total_revenue=Sum('total_amount'),
        bill_count=Count('id')
    )
    
    from django.core.paginator import Paginator
    paginator = Paginator(bills, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'branches': branches,
        'selected_branch': branch_id,
        'start_date': start_date,
        'end_date': end_date,
        'selected_payment': payment_method,
        'query': q,
    }
    return render(request, 'billing/owner_bill_list.html', context)

@login_required
def export_sales_csv(request):
    # Only Owners and Managers can export
    if request.user.role == 'staff':
        return HttpResponse("Unauthorized", status=403)
        
    now = timezone.now()
    # Format: 2026-03-30_12-47-29
    timestamp = now.strftime('%Y-%m-%d_%H-%M-%p') # added AM/PM for better clarity if user prefers
    filename = f"sales_report_{timestamp}.csv"
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    writer.writerow(['Bill ID', 'Branch', 'Staff', 'Customer', 'Phone', 'Amount', 'Payment', 'Date & Time'])
    
    bills = Bill.objects.all().order_by('-created_at')
    # Filter by active branch if manager
    if request.user.role == 'manager':
        bills = bills.filter(branch=request.user.active_branch)
    
    # Optional date filters
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    if start_date:
        bills = bills.filter(created_at__date__gte=start_date)
    if end_date:
        bills = bills.filter(created_at__date__lte=end_date)
        
    for bill in bills.select_related('branch', 'staff'):
        writer.writerow([
            bill.id,
            bill.branch.name if bill.branch else 'N/A',
            bill.staff.username if bill.staff else 'N/A',
            bill.customer_name or 'Guest',
            bill.customer_phone or '',
            bill.total_amount,
            bill.get_payment_method_display(),
            bill.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
        
    return response
