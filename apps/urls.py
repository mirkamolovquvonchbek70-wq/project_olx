from django.urls import path
from apps.views import AnnouncementListView, MainView, CustomLoginView, GoogleLoginView, GoogleCallbackView, \
    ProfileUpdateView, CustomLogoutView, AnnouncementCreateView, category_attributes, RegisterCreateView, \
    AnnouncementSearchView, FavoriteView, toggle_favorite, AnnouncementDetailView, start_chat_page, ChatDetailView

urlpatterns = [
    path('', MainView.as_view(), name='main_page'),
    path('category/<slug:slug>/', AnnouncementListView.as_view(), name='announcement_list_page'),
    path('adding/', AnnouncementCreateView.as_view(), name='add_announcement_page'),
    path("search/", AnnouncementSearchView.as_view(), name="announcement_search_page"),
    path("favorite/", FavoriteView.as_view(), name="favorites_page"),
    path("announcements/<slug:slug>", AnnouncementDetailView.as_view(), name="announcement_detail_page"),
    path("chat/start/<int:announcement_id>/", start_chat_page, name="start_chat_page"),
    path("chat/<int:chat_id>/", ChatDetailView.as_view(), name="chat_detail_page"),

    path("categories/<slug:slug>/attributes/", category_attributes, name="category_attributes"),
    path("favorite/<int:pk>/", toggle_favorite, name="toggle_favorite"),

    path('auth/login/', CustomLoginView.as_view(),  name='login_page'),
    path("auth/google-login", GoogleLoginView.as_view(), name='google_login_page'),
    path("auth/oauth2/callback", GoogleCallbackView.as_view(), name='google_callback_page'),
    path('auth/logout', CustomLogoutView.as_view(), name='logout_page'),
    path('auth/register', RegisterCreateView.as_view(), name='register_page'),
     path('auth/profile', ProfileUpdateView.as_view(), name='profile_page'),



]
