from django.shortcuts import render, redirect

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    return render(request, 'home.html')

# Create your views here.
def terms(request):
    return render(request, "terms.html")

def privacy(request):
    return render(request, "privacy.html")

def faq(request):
    return render(request, "faq.html")