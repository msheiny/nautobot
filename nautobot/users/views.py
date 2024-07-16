import logging
from urllib.parse import parse_qs

from django.contrib import messages
from django.contrib.auth import (
    BACKEND_SESSION_KEY,
    login as auth_login,
    logout as auth_logout,
    update_session_auth_hash,
)
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils.decorators import method_decorator
from django.utils.encoding import iri_to_uri
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import View
from rest_framework.decorators import action

from nautobot.core.forms import ConfirmationForm
from nautobot.core.utils.config import get_settings_or_config
from nautobot.core.utils.lookup import get_table_class_string_from_view_name
from nautobot.core.views.generic import GenericView
from nautobot.core.views.mixins import (
    ObjectChangeLogViewMixin,
    ObjectDestroyViewMixin,
    ObjectDetailViewMixin,
    ObjectEditViewMixin,
    ObjectListViewMixin,
)

from .api.serializers import SavedViewSerializer
from .filters import SavedViewFilterSet
from .forms import AdvancedProfileSettingsForm, LoginForm, PasswordChangeForm, SavedViewForm, TokenForm
from .models import SavedView, Token, UserSavedViewAssociation
from .tables import SavedViewTable

#
# Login/logout
#


class LoginView(View):
    """
    Perform user authentication via the web UI.
    """

    template_name = "login.html"
    use_new_ui = True

    @method_decorator(sensitive_post_parameters("password"))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        form = LoginForm(request)

        if request.user.is_authenticated:
            logger = logging.getLogger("nautobot.auth.login")
            return self.redirect_to_next(request, logger)

        return render(
            request,
            self.template_name,
            {
                "form": form,
            },
        )

    def post(self, request):
        logger = logging.getLogger("nautobot.auth.login")
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            logger.debug("Login form validation was successful")

            # Authenticate user
            auth_login(request, form.get_user())
            messages.info(request, f"Logged in as {request.user}.")

            return self.redirect_to_next(request, logger)

        else:
            logger.debug("Login form validation failed")

        return render(
            request,
            self.template_name,
            {
                "form": form,
            },
        )

    def redirect_to_next(self, request, logger):
        if request.method == "POST":
            redirect_to = request.POST.get("next", reverse("home"))
        else:
            redirect_to = request.GET.get("next", reverse("home"))

        if redirect_to and not url_has_allowed_host_and_scheme(url=redirect_to, allowed_hosts=request.get_host()):
            logger.warning(f"Ignoring unsafe 'next' URL passed to login form: {redirect_to}")
            redirect_to = reverse("home")

        logger.debug(f"Redirecting user to {redirect_to}")
        return HttpResponseRedirect(iri_to_uri(redirect_to))


class LogoutView(View):
    """
    Deauthenticate a web user.
    """

    def get(self, request):
        # Log out the user
        auth_logout(request)
        messages.info(request, "You have logged out.")

        # Delete session key cookie (if set) upon logout
        response = HttpResponseRedirect(reverse("home"))
        response.delete_cookie("session_key")

        return response


#
# User profiles
#


def is_django_auth_user(request):
    return request.session.get(BACKEND_SESSION_KEY, None) == "nautobot.core.authentication.ObjectPermissionBackend"


class ProfileView(GenericView):
    template_name = "users/profile.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {
                "is_django_auth_user": is_django_auth_user(request),
                "active_tab": "profile",
            },
        )


class UserConfigView(GenericView):
    template_name = "users/preferences.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {
                "preferences": request.user.all_config(),
                "active_tab": "preferences",
                "is_django_auth_user": is_django_auth_user(request),
            },
        )

    def post(self, request):
        user = request.user
        data = user.all_config()

        # Delete selected preferences
        for key in request.POST.getlist("pk"):
            if key in data:
                user.clear_config(key)
        user.save()
        messages.success(request, "Your preferences have been updated.")

        return redirect("user:preferences")


class ChangePasswordView(GenericView):
    template_name = "users/change_password.html"

    RESTRICTED_NOTICE = "Remotely authenticated user credentials cannot be changed within Nautobot."

    def get(self, request):
        # Non-Django authentication users cannot change their password here
        if not is_django_auth_user(request):
            messages.warning(
                request,
                self.RESTRICTED_NOTICE,
            )
            return redirect("user:profile")

        form = PasswordChangeForm(user=request.user)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "active_tab": "change_password",
                "is_django_auth_user": is_django_auth_user(request),
            },
        )

    def post(self, request):
        # Non-Django authentication users cannot change their password here
        if not is_django_auth_user(request):
            messages.warning(
                request,
                self.RESTRICTED_NOTICE,
            )
            return redirect("user:profile")

        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, "Your password has been changed successfully.")
            return redirect("user:profile")

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "active_tab": "change_password",
                "is_django_auth_user": is_django_auth_user(request),
            },
        )


#
# Saved Views
#


class SavedViewUIViewSet(
    ObjectDetailViewMixin,
    ObjectChangeLogViewMixin,
    ObjectDestroyViewMixin,
    ObjectEditViewMixin,
    ObjectListViewMixin,
):
    queryset = SavedView.objects.all()
    form_class = SavedViewForm
    filterset_class = SavedViewFilterSet
    serializer_class = SavedViewSerializer
    table_class = SavedViewTable
    action_buttons = ("export",)

    def alter_queryset(self, request):
        """
        Two scenarios we need to handle here:
        1. User can view all saved views with users.view_savedview permission.
        2. User without the permission can only view shared savedviews and his/her own saved views.
        """
        queryset = super().alter_queryset(request)
        user = request.user
        if user.has_perms(["users.view_savedview"]):
            saved_views = queryset.restrict(user, "view")
        else:
            shared_saved_views = queryset.filter(is_shared=True)
            user_owned_saved_views = queryset.filter(owner=user)
            saved_views = shared_saved_views | user_owned_saved_views
        return saved_views

    def get_queryset(self):
        """
        Get the list of items for this view.
        All users should be able to see saved views so we do not apply extra permissions.
        """
        return self.queryset.all()

    def check_permissions(self, request):
        """
        Override this method to not check any permissions.
        Since users with <app_label>.view_<model_name> permissions should be able to view saved views related to this model.
        And those permissions will be enforced in the related view.
        """

    def dispatch(self, request, *args, **kwargs):
        if isinstance(request.user, AnonymousUser):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def extra_message_context(self, obj):
        """
        Context variables for this extra message.
        """
        return {"new_global_default_view": obj}

    def extra_message(self, **kwargs):
        new_global_default_view = kwargs.get("new_global_default_view")
        view_name = new_global_default_view.view
        message = ""
        if new_global_default_view.is_global_default:
            message += f"<br>The global default saved View for '{view_name}' is set to <a href='{new_global_default_view.get_absolute_url()}'>{new_global_default_view.name}</a>."
        return message

    def list(self, request, *args, **kwargs):
        if not request.user.has_perms(["users.view_savedview"]):
            return self.handle_no_permission()
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        The detail view for a saved view should the related ObjectListView with saved configurations applied
        """
        instance = self.get_object()
        list_view_url = reverse(instance.view) + f"?saved_view={instance.pk}"
        return redirect(list_view_url)

    @action(detail=True, name="Set Default", methods=["get"], url_path="set-default", url_name="set_default")
    def set_default(self, request, *args, **kwargs):
        """
        Set current saved view as the the request.user default view. Overriding the global default view if there is one.
        """
        user = request.user
        sv = SavedView.objects.get(pk=kwargs.get("pk", None))
        UserSavedViewAssociation.objects.filter(user=user, view_name=sv.view).delete()
        UserSavedViewAssociation.objects.create(user=user, saved_view=sv, view_name=sv.view)
        list_view_url = sv.get_absolute_url()
        messages.success(
            request, f"Successfully set current view '{sv.name}' as the default '{sv.view}' view for user {user}"
        )
        return redirect(list_view_url)

    @action(detail=True, name="Update Config", methods=["get"], url_path="update-config", url_name="update_config")
    def update_saved_view_config(self, request, *args, **kwargs):
        """
        Extract filter_params, pagination and sort_order from request.GET and apply it to the SavedView specified
        """
        sv = SavedView.objects.get(pk=kwargs.get("pk", None))
        if sv.owner == request.user or request.user.has_perms(["users.change_savedview"]):
            pass
        else:
            messages.error(
                request, f"You do not have the required permission to modify this Saved View owned by {sv.owner}"
            )
            return redirect(self.get_return_url(request, obj=sv))
        table_changes_pending = request.GET.get("table_changes_pending", False)
        all_filters_removed = request.GET.get("all_filters_removed", False)
        pagination_count = request.GET.get("per_page", None)
        if pagination_count is not None:
            sv.config["pagination_count"] = int(pagination_count)
        sort_order = request.GET.getlist("sort", [])
        if sort_order:
            sv.config["sort_order"] = sort_order

        filter_params = {}
        for key in request.GET:
            if key in self.non_filter_params:
                continue
            # TODO: this is fragile, other single-value filters will also be unhappy if given a list
            if key == "q":
                filter_params[key] = request.GET.get(key)
            else:
                filter_params[key] = request.GET.getlist(key)

        if filter_params:
            sv.config["filter_params"] = filter_params
        elif all_filters_removed:
            sv.config["filter_params"] = {}

        if table_changes_pending:
            table_class = get_table_class_string_from_view_name(sv.view)
            if table_class:
                if sv.config.get("table_config", None) is None:
                    sv.config["table_config"] = {}
                sv.config["table_config"][f"{table_class}"] = request.user.get_config(f"tables.{table_class}")

        sv.validated_save()
        list_view_url = sv.get_absolute_url()
        messages.success(request, f"Successfully updated current view {sv.name}")
        return redirect(list_view_url)

    def create(self, request, *args, **kwargs):
        """
        This method will extract filter_params, pagination and sort_order from request.GET
        and the name of the new SavedView from request.POST to create a new SavedView.
        """
        name = request.POST.get("name")
        is_shared = request.POST.get("is_shared", False)
        if is_shared:
            is_shared = True
        params = request.POST.get("params", "")

        param_dict = parse_qs(params)

        single_value_params = ["saved_view", "table_changes_pending", "all_filters_removed", "q", "per_page"]
        for key in param_dict.keys():
            if key in single_value_params:
                param_dict[key] = param_dict[key][0]

        derived_view_pk = param_dict.get("saved_view", None)
        derived_instance = None
        if derived_view_pk:
            derived_instance = self.get_queryset().get(pk=derived_view_pk)
        view_name = request.POST.get("view")
        try:
            reverse(view_name)
        except NoReverseMatch:
            messages.error(request, f"Invalid view name {view_name} specified.")
            if derived_view_pk:
                return redirect(self.get_return_url(request, obj=derived_instance))
            else:
                return redirect(self.get_return_url(request))
        table_changes_pending = param_dict.get("table_changes_pending", False)
        all_filters_removed = param_dict.get("all_filters_removed", False)
        try:
            sv = SavedView.objects.create(name=name, owner=request.user, view=view_name, is_shared=is_shared)
        except IntegrityError:
            messages.error(request, f"You already have a Saved View named '{name}' for this view '{view_name}'")
            if derived_view_pk:
                return redirect(self.get_return_url(request, obj=derived_instance))
            else:
                return redirect(reverse(view_name))
        pagination_count = param_dict.get("per_page", None)
        if not pagination_count:
            if derived_instance and derived_instance.config.get("pagination_count", None):
                pagination_count = derived_instance.config["pagination_count"]
            else:
                pagination_count = get_settings_or_config("PAGINATE_COUNT")
        sv.config["pagination_count"] = int(pagination_count)
        sort_order = param_dict.get("sort", [])
        if not sort_order:
            if derived_instance:
                sort_order = derived_instance.config.get("sort_order", [])
        sv.config["sort_order"] = sort_order

        sv.config["filter_params"] = {}
        for key in param_dict:
            if key in [*self.non_filter_params, "view"]:
                continue
            sv.config["filter_params"][key] = param_dict.get(key)
        if not sv.config["filter_params"]:
            if derived_instance and all_filters_removed:
                sv.config["filter_params"] = {}
            elif derived_instance:
                sv.config["filter_params"] = derived_instance.config["filter_params"]

        table_class = get_table_class_string_from_view_name(view_name)
        sv.config["table_config"] = {}
        if table_class:
            if table_changes_pending or derived_instance is None:
                sv.config["table_config"][f"{table_class}"] = request.user.get_config(f"tables.{table_class}")
            elif derived_instance.config.get("table_config") and derived_instance.config["table_config"].get(
                f"{table_class}"
            ):
                sv.config["table_config"][f"{table_class}"] = derived_instance.config["table_config"][f"{table_class}"]
        try:
            sv.validated_save()
            list_view_url = sv.get_absolute_url()
            message = f"Successfully created new Saved View '{sv.name}'."
            messages.success(request, message)
            return redirect(list_view_url)
        except ValidationError as e:
            messages.error(request, e)
            return redirect(self.get_return_url(request))

    def destroy(self, request, *args, **kwargs):
        """
        request.GET: render the ObjectDeleteConfirmationForm which is passed to NautobotHTMLRenderer as Response.
        request.POST: call perform_destroy() which validates the form and perform the action of delete.
        Override to add more variables to Response
        """
        sv = SavedView.objects.get(pk=kwargs.get("pk", None))
        if sv.owner == request.user or request.user.has_perms(["extras.delete_savedview"]):
            pass
        else:
            messages.error(
                request, f"You do not have the required permission to delete this Saved View owned by {sv.owner}"
            )
            return redirect(self.get_return_url(request, obj=sv))
        return super().destroy(request, *args, **kwargs)


#
# API tokens
#


class TokenListView(GenericView):
    def get(self, request):
        tokens = Token.objects.filter(user=request.user)

        return render(
            request,
            "users/api_tokens.html",
            {
                "tokens": tokens,
                "active_tab": "api_tokens",
                "is_django_auth_user": is_django_auth_user(request),
            },
        )


class TokenEditView(GenericView):
    def get(self, request, pk=None):
        if pk is not None:
            if not request.user.has_perm("users.change_token"):
                return HttpResponseForbidden()
            token = get_object_or_404(Token.objects.filter(user=request.user), pk=pk)
        else:
            if not request.user.has_perm("users.add_token"):
                return HttpResponseForbidden()
            token = Token(user=request.user)

        form = TokenForm(instance=token)

        return render(
            request,
            "generic/object_create.html",
            {
                "obj": token,
                "obj_type": token._meta.verbose_name,
                "form": form,
                "return_url": reverse("user:token_list"),
                "editing": token.present_in_database,
            },
        )

    def post(self, request, pk=None):
        if pk is not None:
            token = get_object_or_404(Token.objects.filter(user=request.user), pk=pk)
            form = TokenForm(request.POST, instance=token)
        else:
            token = Token()
            form = TokenForm(request.POST)

        if form.is_valid():
            token = form.save(commit=False)
            token.user = request.user
            token.save()

            msg = f"Modified token {token}" if pk else f"Created token {token}"
            messages.success(request, msg)

            if "_addanother" in request.POST:
                return redirect(request.path)
            else:
                return redirect("user:token_list")

        return render(
            request,
            "generic/object_create.html",
            {
                "obj": token,
                "obj_type": token._meta.verbose_name,
                "form": form,
                "return_url": reverse("user:token_list"),
                "editing": token.present_in_database,
            },
        )


class TokenDeleteView(GenericView):
    def get(self, request, pk):
        token = get_object_or_404(Token.objects.filter(user=request.user), pk=pk)
        initial_data = {
            "return_url": reverse("user:token_list"),
        }
        form = ConfirmationForm(initial=initial_data)

        return render(
            request,
            "generic/object_delete.html",
            {
                "obj": token,
                "obj_type": token._meta.verbose_name,
                "form": form,
                "return_url": reverse("user:token_list"),
            },
        )

    def post(self, request, pk):
        token = get_object_or_404(Token.objects.filter(user=request.user), pk=pk)
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            token.delete()
            messages.success(request, "Token deleted")
            return redirect("user:token_list")

        return render(
            request,
            "generic/object_delete.html",
            {
                "obj": token,
                "obj_type": token._meta.verbose_name,
                "form": form,
                "return_url": reverse("user:token_list"),
            },
        )


#
# Advanced Profile Settings
#


class AdvancedProfileSettingsEditView(GenericView):
    template_name = "users/advanced_settings_edit.html"

    def get(self, request):
        silk_record_requests = request.session.get("silk_record_requests", False)
        form = AdvancedProfileSettingsForm(initial={"request_profiling": silk_record_requests})

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "active_tab": "advanced_settings",
                "return_url": reverse("user:advanced_settings_edit"),
                "is_django_auth_user": is_django_auth_user(request),
            },
        )

    def post(self, request):
        form = AdvancedProfileSettingsForm(request.POST)

        if form.is_valid():
            silk_record_requests = form.cleaned_data["request_profiling"]

            # Set the value for `silk_record_requests` in the session
            request.session["silk_record_requests"] = silk_record_requests

            if silk_record_requests:
                msg = "Enabled request profiling for the duration of the login session."
            else:
                msg = "Disabled request profiling."
            messages.success(request, msg)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "active_tab": "advanced_settings",
                "return_url": reverse("user:advanced_settings_edit"),
                "is_django_auth_user": is_django_auth_user(request),
            },
        )
