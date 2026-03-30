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

@login_required
def product_list(request):
    if request.user.role == 'staff':
        return redirect('dashboard')
    products = Product.objects.all().order_by('name')
    return render(request, 'core/product_list.html', {'products': products})

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
            
            # Automatically create inventory for all branches
            from core.models import Branch
            for branch in Branch.objects.all():
                stock = initial_stock if branch == initial_branch else 0
                Inventory.objects.get_or_create(branch=branch, product=product, defaults={'stock_quantity': stock})
                
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
