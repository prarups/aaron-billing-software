from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from .models import Inventory
from core.models import Branch, Product
from django import forms

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['stock_quantity', 'low_stock_threshold']
        widgets = {
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control rounded-pill'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control rounded-pill'}),
        }

@login_required
def manager_inventory_list(request):
    if request.user.role != 'manager' and request.user.role != 'owner':
        return redirect('dashboard')
    
    branch = request.user.active_branch
    inventory = Inventory.objects.filter(branch=branch).select_related('product')
    return render(request, 'inventory/manager_list.html', {'inventory': inventory})

@login_required
def update_inventory(request, pk):
    inventory = get_object_or_404(Inventory, pk=pk, branch=request.user.active_branch)
    if request.method == 'POST':
        form = InventoryForm(request.POST, instance=inventory)
        if form.is_valid():
            form.save()
            return redirect('manager_inventory_list')
    else:
        form = InventoryForm(instance=inventory)
    
    return render(request, 'inventory/update.html', {'form': form, 'inventory': inventory})

@login_required
def stock_in(request, pk):
    inventory = get_object_or_404(Inventory, pk=pk, branch=request.user.active_branch)
    if request.method == 'POST':
        add_qty = int(request.POST.get('add_quantity', 0))
        if add_qty > 0:
            inventory.stock_quantity += add_qty
            inventory.save()
            return redirect('manager_inventory_list')
    return render(request, 'inventory/stock_in.html', {'inventory': inventory})

@login_required
def owner_inventory_view(request):
    if request.user.role != 'owner':
        return redirect('dashboard')
    
    inventory_items = Inventory.objects.select_related('product', 'branch').order_by('branch', 'product__name')
    
    branch_id = request.GET.get('branch')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if branch_id and branch_id != 'None':
        inventory_items = inventory_items.filter(branch_id=branch_id)
        
    if start_date:
        try:
            inventory_items = inventory_items.filter(last_updated__date__gte=start_date)
        except ValueError:
            pass

    if end_date:
        try:
            inventory_items = inventory_items.filter(last_updated__date__lte=end_date)
        except ValueError:
            pass
            
    branches = Branch.objects.all()

    from django.core.paginator import Paginator
    paginator = Paginator(inventory_items, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'inventory/owner_list.html', {
        'page_obj': page_obj,
        'branches': branches,
        'selected_branch': branch_id,
        'start_date': start_date or '',
        'end_date': end_date or ''
    })

@login_required
def get_or_create_inventory(request, product_id):
    """Redirect to the inventory update page, creating the record if it doesn't exist."""
    branch = request.user.active_branch
    if not branch:
        return redirect('dashboard')
    
    product = get_object_or_404(Product, id=product_id)
    
    inventory, created = Inventory.objects.get_or_create(
        branch=branch, 
        product=product,
        defaults={'stock_quantity': 0}
    )
    
    return redirect('update_inventory', pk=inventory.pk)

@login_required
def update_inventory_stock_ajax(request, product_id):
    """Update stock for the active branch via AJAX."""
    branch = request.user.active_branch
    if not branch:
        return JsonResponse({'error': 'No active branch'}, status=400)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_stock = data.get('stock')
            if new_stock is not None:
                product = get_object_or_404(Product, id=product_id)
                inventory, created = Inventory.objects.get_or_create(
                    branch=branch, 
                    product=product,
                    defaults={'stock_quantity': 0}
                )
                inventory.stock_quantity = int(new_stock)
                inventory.save()
                return JsonResponse({'success': True, 'stock': inventory.stock_quantity})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'Invalid request'}, status=405)
