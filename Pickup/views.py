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

from .models import HomeSlider

def home(request):
    # if request.user.is_authenticated:
    #     return redirect('dashboard')

    sliders = (
        HomeSlider.objects
        .filter(is_active=True)
        .order_by('-created_at')[:5]  
    )

    return render(request, 'home.html', {
        'sliders': sliders
    })

# home/views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import HomeSlider
from .forms import HomeSliderForm
from .serializers import HomeSliderSerializer

def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

class SliderListView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_admin(request.user):
            return redirect('dashboard')

        sliders = HomeSlider.objects.order_by('-created_at')
        return render(request, 'home/slider_list.html', {'sliders': sliders})

class SliderCreateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (request.user.is_superuser or request.user.role == 'admin'):
            return redirect('dashboard')

        return render(
            request,
            'home/slider_form.html',
            {'form': HomeSliderForm()}
        )

    def post(self, request):
        if not (request.user.is_superuser or request.user.role == 'admin'):
            return redirect('dashboard')

        form = HomeSliderForm(request.POST, request.FILES)
        serializer = HomeSliderSerializer(data=request.data)  # ✅ FIX

        if not serializer.is_valid():
            return render(
                request,
                'home/slider_form.html',
                {
                    'form': form,
                    'error': serializer.errors
                }
            )

        serializer.save()
        messages.success(request, 'Slider created successfully')
        return redirect('slider_list')
class SliderUpdateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if not (request.user.is_superuser or request.user.role == 'admin'):
            return redirect('dashboard')

        slider = get_object_or_404(HomeSlider, pk=pk)

        return render(
            request,
            'home/slider_form.html',
            {
                'form': HomeSliderForm(instance=slider),
                'slider': slider,
                'edit': True
            }
        )

    def post(self, request, pk):
        if not (request.user.is_superuser or request.user.role == 'admin'):
            return redirect('dashboard')

        slider = get_object_or_404(HomeSlider, pk=pk)

        # 🔒 Preserve old image
        current_image = slider.image

        form = HomeSliderForm(request.POST, request.FILES, instance=slider)
        serializer = HomeSliderSerializer(
            slider,
            data=request.data,
            partial=True
        )

        if not serializer.is_valid():
            return render(
                request,
                'home/slider_form.html',
                {
                    'form': form,
                    'slider': slider,
                    'edit': True,
                    'error': serializer.errors
                }
            )

        slider = serializer.save()

        # 🔥 Preserve image if not uploaded again
        if 'image' not in request.FILES:
            slider.image = current_image

        slider.save()
        messages.success(request, 'Slider updated successfully')
        return redirect('slider_list')

class SliderDeleteView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not is_admin(request.user):
            return redirect('dashboard')

        slider = get_object_or_404(HomeSlider, pk=pk)
        slider.delete()
        messages.success(request, 'Slider deleted')
        return redirect('slider_list')
