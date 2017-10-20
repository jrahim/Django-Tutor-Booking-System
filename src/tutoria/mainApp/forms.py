from django import forms


class ImageForm(forms.Form):
    docfile = forms.ImageField(
        label='Upload your avatar',
    )
