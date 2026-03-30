from django import forms
from django.contrib.auth.forms import AuthenticationForm
from core.models import Branch
from .models import User

class CustomAuthenticationForm(AuthenticationForm):
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        required=False,
        empty_label="Select Branch",
        widget=forms.Select(attrs={'class': 'form-select rounded-3'})
    )

    def clean(self):
        cleaned_data = super().clean()
        user = self.get_user()
        
        if user:
            role_selected = cleaned_data.get('role')
            branch_selected = cleaned_data.get('branch')

            # Ensure the user has the selected role
            if user.role != role_selected:
                raise forms.ValidationError("You do not have the required permissions for this role.")

            # If Staff or Manager is selected, a branch must be chosen (unless user is already strictly bound differently)
            # Actually, Owner can select Owner and no branch is needed.
            if role_selected in ['staff', 'manager']:
                if not branch_selected:
                    # Look for existing active_branch on the user
                    if user.active_branch:
                        cleaned_data['branch'] = user.active_branch
                    else:
                        raise forms.ValidationError("Please select a branch to login.")
                else:
                    # Verify user is assigned to this branch
                    if not user.is_owner() and not user.branches.filter(id=branch_selected.id).exists():
                         raise forms.ValidationError(f"You are not assigned to the {branch_selected.name} branch.")
                    
                    # Update user's active branch
                    user.active_branch = branch_selected
                    user.save()
        return cleaned_data
