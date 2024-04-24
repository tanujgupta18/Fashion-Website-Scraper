from django import forms

class ScrapeForm(forms.Form):
    url = forms.URLField(label='Enter the URL to scrape')