from django import forms
from users.models import Project
from celerytasks.tasks import ingest_csv


class CSVUploader(forms.Form):
    csv = forms.FileField()
    project = forms.ModelChoiceField(queryset=Project.objects.all())

    def save(self):
        ingest_csv(self.cleaned_data["csv"], self.cleaned_data["project"])
