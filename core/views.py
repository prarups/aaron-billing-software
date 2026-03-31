from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Branch
from django import forms
from inventory.models import Inventory

class ProductForm(forms.ModelForm):
    initial_branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(), 
        required=False,
        label="Branch Location",
        widget=forms.Select(attrs={'class': 'form-select rounded-pill'})
    )
    initial_stock = forms.IntegerField(
        required=False, 
        initial=0,
        label="Initial Stock Quantity",
        widget=forms.NumberInput(attrs={'class': 'form-control rounded-pill'})
    )

    class Meta:
        model = Product
        fields = ['name', 'barcode', 'price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control rounded-pill'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control rounded-pill'}),
            'price': forms.NumberInput(attrs={'class': 'form-control rounded-pill'}),
        }

class UnifiedProductForm(forms.ModelForm):
    stock_quantity = forms.IntegerField(
        label="Current Stock",
        widget=forms.NumberInput(attrs={'class': 'form-control rounded-pill'})
    )
    low_stock_threshold = forms.IntegerField(
        label="Low Stock Alert Level",
        widget=forms.NumberInput(attrs={'class': 'form-control rounded-pill'})
    )

    class Meta:
        model = Product
        fields = ['name', 'barcode', 'price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control rounded-pill'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control rounded-pill'}),
            'price': forms.NumberInput(attrs={'class': 'form-control rounded-pill'}),
        }

@login_required
def product_list(request):
    if request.user.role == 'staff':
        return redirect('dashboard')
    
    from django.db.models import OuterRef, Subquery, Value
    from django.db.models.functions import Coalesce
    from inventory.models import Inventory

    products = Product.objects.annotate(
        stock=Coalesce(
            Subquery(
                Inventory.objects.filter(
                    product=OuterRef('pk'), 
                    branch=request.user.active_branch
                ).values('stock_quantity')[:1]
            ),
            Value(0)
        )
    )
    
    active_filter = request.GET.get('filter')
    if active_filter == 'zero_stock':
        products = products.filter(stock=0)
    
    products = products.order_by('name')
    
    return render(request, 'core/product_list.html', {
        'products': products,
        'active_filter': active_filter
    })

@login_required
def product_create(request):
    if request.user.role == 'staff':
        return redirect('dashboard')
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            initial_branch = form.cleaned_data.get('initial_branch')
            initial_stock = form.cleaned_data.get('initial_stock') or 0
            
            # Create inventory only for the chosen branch
            if initial_branch:
                Inventory.objects.get_or_create(
                    branch=initial_branch, 
                    product=product, 
                    defaults={'stock_quantity': initial_stock}
                )
                
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'core/product_form.html', {'form': form, 'action': 'Add New'})

@login_required
def product_update(request, pk):
    if request.user.role == 'staff':
        return redirect('dashboard')
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'core/product_form.html', {'form': form, 'action': 'Edit'})

from django.http import JsonResponse
import json

@login_required
def update_product_price_ajax(request, pk):
    if request.user.role == 'staff':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_price = data.get('price')
            if new_price is not None:
                product = get_object_or_404(Product, pk=pk)
                product.price = new_price
                product.save()
                return JsonResponse({'success': True, 'price': float(product.price)})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    return JsonResponse({'error': 'Invalid request'}, status=405)

@login_required
def unified_product_edit(request, pk):
    if request.user.role == 'staff':
        return redirect('dashboard')
        
    product = get_object_or_404(Product, pk=pk)
    branch = request.user.active_branch
    
    if not branch:
        return redirect('product_list') # Should ideally show an error
        
    inventory, created = Inventory.objects.get_or_create(
        branch=branch, 
        product=product,
        defaults={'stock_quantity': 0, 'low_stock_threshold': 10}
    )
    
    if request.method == 'POST':
        form = UnifiedProductForm(request.POST, instance=product)
        if form.is_valid():
            # Save product details
            product = form.save()
            # Save inventory details
            inventory.stock_quantity = form.cleaned_data['stock_quantity']
            inventory.low_stock_threshold = form.cleaned_data['low_stock_threshold']
            inventory.save()
            return redirect('product_list')
    else:
        # Initialize form with both product and inventory data
        form = UnifiedProductForm(instance=product, initial={
            'stock_quantity': inventory.stock_quantity,
            'low_stock_threshold': inventory.low_stock_threshold
        })
        
    return render(request, 'core/product_form.html', {
        'form': form, 
        'action': 'Edit', 
        'product': product
    })
