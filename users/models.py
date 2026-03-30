from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='staff')
    # Managers and Staff can be assigned to multiple branches
    branches = models.ManyToManyField('core.Branch', blank=True, related_name='assigned_users')
    # The branch currently selected for the session
    active_branch = models.ForeignKey('core.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='active_users')

    def is_owner(self):
        return self.role == 'owner'

    def is_manager(self):
        return self.role == 'manager'

    def is_staff_role(self):
        return self.role == 'staff'

    def get_accessible_branches(self):
        """Returns the branches this user is authorized to work in."""
        from core.models import Branch
        if self.is_owner():
            return Branch.objects.all()
        return self.branches.all()
