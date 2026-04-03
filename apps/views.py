import urllib.parse
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
import requests
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.decorators import login_required
from apps.forms import AnnouncementModelForm, RegisterModelForm, EmailLoginForm
from apps.models import Announcement, Category, User, Region, City
from django.views.generic import ListView
from apps.models.announcements import AnnouncementImage
from root import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django_filters.views import FilterView
from apps.filters import AnnouncementFilterSet
from apps.models import Favorite



class MainView(ListView):
    template_name = 'apps/main.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(parent=None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["regions"] = Region.objects.prefetch_related('cities')
        announcements = Announcement.objects.filter(
            product_type=Announcement.AnnouncementType.VIP
        )

        q = self.request.GET.get("q")
        if q:
            announcements = announcements.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q)
            ).distinct()

        context['announcements'] = announcements
        context['search_value'] = q or ""
        return context


class AnnouncementSearchView(FilterView):
    template_name = "apps/announcement-list.html"
    context_object_name = "announcements"
    filterset_class = AnnouncementFilterSet

    def get_queryset(self):
        queryset = Announcement.objects.all().select_related("city", "city__region")

        q = self.request.GET.get("q")
        region = self.request.GET.get("region")
        city = self.request.GET.get("city")

        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q  )
            )

        if region:
            queryset = queryset.filter(city__region__name=region)

        if city:
            queryset = queryset.filter(city__name=city)

        return queryset.distinct()

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs["category"] = None
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dynamic_fields"] = self.filterset.dynamic_fields
        context["top_categories"] = Category.objects.filter(parent=None)
        context["current_category"] = None
        context["search_value"] = self.request.GET.get("q", "")
        context["regions"] = Region.objects.prefetch_related('cities')
        return context





class AnnouncementListView(FilterView):
    template_name = "apps/announcement-list.html"
    context_object_name = "announcements"
    filterset_class = AnnouncementFilterSet

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(Category, slug=self.kwargs.get("slug"))
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        categories = self.category.get_descendants(include_self=True)
        return (
            Announcement.objects
            .filter(category__in=categories)
            .prefetch_related("images")
        )

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs["category"] = self.category
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dynamic_fields"] = self.filterset.dynamic_fields
        context["top_categories"] = Category.objects.filter(parent=None)
        context["current_category"] = self.category
        context["search_value"] = self.request.GET.get("q", "")

        if self.request.user.is_authenticated:
            context["favorite_ids"] = set(
                Favorite.objects.filter(user=self.request.user)
                .values_list("announcement_id", flat=True)
            )
        else:
            context["favorite_ids"] = set()

        return context


class FavoriteView(LoginRequiredMixin, ListView):
    template_name = "apps/favorites.html"
    context_object_name = "favorites"

    def get_queryset(self):
        return (
            Announcement.objects
            .filter(favorited_by__user=self.request.user)
            .prefetch_related("images")
            .distinct()
            .order_by("-favorited_by__created_at")
        )


@require_POST
@login_required
def toggle_favorite(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)

    favorite_qs = Favorite.objects.filter(
        user=request.user,
        announcement=announcement
    )

    if favorite_qs.exists():
        favorite_qs.delete()
        is_favorite = False
    else:
        Favorite.objects.create(
            user=request.user,
            announcement=announcement
        )
        is_favorite = True

    return JsonResponse({
        "success": True,
        "is_favorite": is_favorite,
        "announcement_id": announcement.pk,
    })




class CustomLoginView(LoginView):
    template_name = 'apps/auth/login.html'
    authentication_form = EmailLoginForm
    success_url = reverse_lazy('main_page')
    redirect_authenticated_user = True

class RegisterCreateView(CreateView):
    template_name = 'apps/auth/register.html'
    form_class = RegisterModelForm
    success_url = reverse_lazy('login_page')


class GoogleLoginView(View):
    def get(self, request):
        scope = "email profile"
        auth_url = (
            f"https://accounts.google.com/o/oauth2/auth?response_type=code"
            f"&client_id={settings.GOOGLE_CLIENT_ID}"
            f"&redirect_uri={urllib.parse.quote(settings.GOOGLE_REDIRECT_URI)}"
            f"&scope={urllib.parse.quote(scope)}"
        )
        return redirect(auth_url)


class GoogleCallbackView(View):
    def get(self, request):
        code = request.GET.get("code")

        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        token_res = requests.post("https://oauth2.googleapis.com/token", data=token_data).json()
        access_token = token_res.get("access_token")

        response = requests.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if response.status_code == 200:
            info = response.json()
            email = info["email"]
            name = info["name"]

            user, created = User.objects.get_or_create(
                email=email,
                defaults={"first_name": name}
            )
            if not user.is_valid_password or created:
                user.set_unusable_password()
                user.save(update_fields=['password'])
            login(request, user)

            return redirect('main_page')
        return redirect('login_page')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    queryset = User.objects.all()
    template_name = 'apps/auth/profile.html'
    fields = ['first_name', 'last_name']
    success_url = reverse_lazy('profile_page')

    def get_object(self, queryset=None):
        return self.request.user


class CustomLogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('main_page')


class AnnouncementCreateView(LoginRequiredMixin, CreateView):
    model = Announcement
    template_name = 'apps/add_announcement.html'
    form_class = AnnouncementModelForm
    success_url = reverse_lazy('profile_page')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['top_categories'] = Category.objects.filter(parent=None)
        return context

    def form_valid(self, form):

        form.instance.user = self.request.user

        response = super().form_valid(form)

        images = self.request.FILES.getlist("images")
        for img in images:
            AnnouncementImage.objects.create(
                product=self.object,
                image=img
            )

        return response


def category_attributes(request, slug):
    cat = get_object_or_404(Category, slug=slug)
    return JsonResponse(cat.attribute or [], safe=False)



