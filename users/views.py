from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import models
from django.db.models import Sum, Count, F, Q
from django.views.generic import TemplateView
from billing.models import Bill
from core.models import Branch
from inventory.models import Inventory

@login_required
def dashboard_redirect(request):
    if request.user.role == 'owner':
        return redirect('owner_dashboard')
    elif request.user.role == 'manager':
        return redirect('manager_dashboard')
    else:
        return redirect('staff_dashboard')

@login_required
def switch_branch(request):
    """Allows Managers/Owners to switch their active session branch."""
    if request.method == 'POST':
        branch_id = request.POST.get('branch_id')
        if branch_id:
            branch = get_object_or_404(Branch, id=branch_id)
            # Permission check
            if request.user.is_owner() or request.user.branches.filter(id=branch.id).exists():
                request.user.active_branch = branch
                request.user.save()
    
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

class OwnerDashboardView(TemplateView):
    template_name = 'dashboards/owner.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Overall Stats
        today_bills = Bill.objects.filter(created_at__date=today)
        context['total_sales_today'] = today_bills.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        context['transaction_count_today'] = today_bills.count()
        context['branch_count'] = Branch.objects.count()
        context['low_stock_count'] = Inventory.objects.filter(stock_quantity__lte=models.F('low_stock_threshold')).count()
        
        # Branch performance
        branches = Branch.objects.annotate(
            today_sales=Sum('bills__total_amount', filter=models.Q(bills__created_at__date=today))
        )
        context['branches'] = branches
        context['recent_bills'] = Bill.objects.order_by('-created_at')[:5]
        return context

class ManagerDashboardView(TemplateView):
    template_name = 'dashboards/manager.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        branch = self.request.user.active_branch
        if not branch:
            return context
            
        today = timezone.now().date()
        branch_bills = Bill.objects.filter(branch=branch, created_at__date=today)
        
        context['branch_sales_today'] = branch_bills.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        context['inventory_count'] = Inventory.objects.filter(branch=branch).count()
        context['staff_count'] = branch.assigned_users.filter(role='staff').count()
        
        context['low_stock_items'] = Inventory.objects.filter(
            branch=branch, 
            stock_quantity__lte=models.F('low_stock_threshold')
        ).select_related('product')
        
        context['recent_branch_bills'] = Bill.objects.filter(branch=branch).order_by('-created_at')[:5]
        return context

class StaffDashboardView(TemplateView):
    template_name = 'dashboards/staff.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        branch = self.request.user.active_branch
        staff_bills = Bill.objects.filter(staff=self.request.user, branch=branch, created_at__date=today)
        
        context['my_sales_today'] = staff_bills.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        context['my_bill_count'] = staff_bills.count()
        context['recent_my_bills'] = staff_bills.order_by('-created_at')[:5]
        context['today_date'] = today.isoformat()
        return context
