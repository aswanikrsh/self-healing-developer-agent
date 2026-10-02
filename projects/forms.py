from django import forms


class ProjectForm(forms.Form):

    name = forms.CharField(
        max_length=200
    )

    project_path = forms.CharField(
        max_length=500
    )


class DebugForm(forms.Form):

    error_message = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 10,
                "placeholder": "Paste the error or traceback here..."
            }
        )
    )