from django.urls import path

from portfolio_builder.portfolio import views as portf_views


urlpatterns = [
    path(r"^add_portf$/", portf_views.add_portfolio, name="add_portf"),
    path(r"^del_portf$/", portf_views.del_portfolio, name="del_portf"),
    path(r"^(?P<portf_name>\w+)/add_pos/$", portf_views.add_position, name="add_pos"),
    path(r"^(?P<portf_name>\w+)/(?P<ticker>\w+)/upd_pos/$", portf_views.upd_position, name="upd_pos"),
    path(r"^(?P<portf_name>\w+)/(?P<ticker>\w+)/del_pos/$", portf_views.del_position, name="del_pos"),
    path(r"", portf_views.index, name="index"),
]
