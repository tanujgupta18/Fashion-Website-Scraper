from django import forms

class ScrapeForm(forms.Form):
    url = forms.URLField(label="Enter URL to scrape", required=True)
