from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse
from werkzeug.wrappers.response import Response

from portfolio_builder.portfolio.forms import (
    AddPortfolioForm, SelectPortfolioForm, 
    AddPositionForm, UpdatePositionForm
)
from portfolio_builder.portfolio.models import (
    Portfolio, Position, Security
)


def flash_errors(form: forms.Form):
    """Flash all errors for a form."""
    for field, errors in form.errors.items():
        for error in errors:
            messages.add_message(
                messages.ERROR,
                f"{getattr(form, field).label.text} - {error}",  # type: ignore
            )
            

@login_required
def index(request) -> str:
    """
    Renders the portfolio page and handles portfolio-related actions.

    Returns:
        str: A rendered HTML template with the necessary data.
    """
    portf_names = [
        item.name
        for item in Portfolio.custom_obj.get_items(
            filters=Q(user_id=1) # Change for user.id next
        )
    ]
    add_portf_form = AddPortfolioForm()
    sel_portf_form = SelectPortfolioForm()
    add_pos_form = AddPositionForm()
    upd_pos_form = UpdatePositionForm()
    sel_portf_form.name.choices =  [
        (item, item)
        for item in portf_names
    ]
    if sel_portf_form.is_valid():
        curr_portf_name = sel_portf_form.name.data # Current portfolio name
    else:
        curr_portf_name = next(iter(portf_names), '')
    positions = Position.custom_obj.get_items(filters=(
        Q(portfolio_id__user_id=1) & # Change for user.id next
        Q(portfolio_id__name=curr_portf_name) &
        Q(is_last_trade=True)
    ))
    securities = Security.custom_obj.get_items(filters=Q(True))
    return render(
        "portfolio.html", 
        sel_portf_form=sel_portf_form,
        add_portf_form=add_portf_form,
        add_pos_form=add_pos_form,
        upd_pos_form=upd_pos_form,
        curr_portf_name=curr_portf_name,
        portf_names=portf_names,
        securities=securities,
        positions=positions,
    )


@login_required
def add_portfolio(request) -> Response:
    """
    Adds a new portfolio to the database.

    Returns:
        Response: A redirect response to the 'index' url name.
    """
    form = AddPortfolioForm()
    if form.is_valid():
        portf_name = form.name.data 
        new_item = Portfolio(
            user_id=1, # Change for user.id next
            name=portf_name, 
        )
        new_item.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            f"The portfolio '{portf_name}' has been added."
        )
    elif form.errors:
        flash_errors(form)
    return redirect(reverse('index'))


@login_required
def del_portfolio(request) -> Response:
    """
    Deletes a portfolio from the database.

    :return: A redirect response to the 'index' url name.
    """
    portf_names = [
        item.name
        for item in Portfolio.custom_obj.get_items(
            filters=Q(user_id=1) # Change for user.id next
        )
    ]
    form = SelectPortfolioForm()
    form.name.choices =  [
        (item, item)
        for item in portf_names
    ]
    if form.is_valid():
        portf_name = form.name.data
        portfolio = Portfolio.custom_obj.get_first_item(
            filters=Q(name=portf_name)
        )
        if portfolio is None:
            messages.add_message(
                request,
                messages.ERROR,
                f"The portfolio '{portf_name}' does not exist."
            )
        else:
            portfolio.delete()
            messages.add_message(
                request,
                messages.SUCCESS,
                f"The portfolio '{portf_name}' has been deleted."
            )
    elif form.errors:
        flash_errors(form)
    return redirect(reverse('index'))


@login_required
def add_position(request, portf_name: str) -> Response:
    """
    Adds a new item to a specific portfolio in the database.

    Args:
        portf_name (str): The name of the portfolio to add the item to.

    Returns:
        Response: A redirect response to the 'index' url name.
    """
    form = AddPositionForm()
    if form.is_valid():
        portfolio = Portfolio.custom_obj.get_first_item(
            filters=Q(name=portf_name)
        )
        if portfolio is None:
            messages.add_message(
                request,
                messages.ERROR,
                f"The portfolio '{portf_name}' does not exist."
            )
        else:
            new_item = Position(
                ticker=form.ticker.data, 
                quantity=form.quantity.data,
                price=form.price.data, 
                side=form.side.data,  
                trade_date=form.trade_date.data,
                comments=form.comments.data, 
                portfolio_id=portfolio.id
            )
            new_item.save()
            messages.add_message(
                messages.SUCCESS,
                f"The ticker '{new_item.ticker}' has been added to the portfolio."
            )
    elif form.errors:
        flash_errors(form)
    return redirect(reverse("index"))


@login_required
def upd_position(request, portf_name: str, ticker: str) -> Response:
    """
    Updates a portfolio item, identified by the ticker, 
    of a specific portfolio in the database.

    Args:
        portf_name (str): The name of the portfolio to update.
        ticker (str): The ticker symbol of the portfolio item to update.

    Returns:
        Response: Redirects the user to the portfolio index page.
    """
    form = UpdatePositionForm()
    if form.is_valid():
        last_item = Position.custom_obj.get_first_item(filters=(
            Q(portfolio_id__user_id=1) & # Change for user.id next
            Q(name=portf_name) & 
            Q(ticker=ticker) &
            Q(is_last_trade=True)
        ))
        if last_item is None:
            messages.add_message(
                request,
                messages.ERROR,
                f"There are no items of ticker '{ticker}' to update."
            )
        else:
            last_item.is_last_trade = False
            new_item = Position(
                ticker=form.ticker.data, 
                quantity=form.quantity.data,
                price=form.price.data, 
                side=form.side.data, 
                trade_date=form.trade_date.data,
                comments=form.comments.data,
                portfolio_id=last_item.portfolio_id
            )
            last_item.save()
            new_item.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                f"The ticker '{new_item.ticker}' has been updated."
            )
    elif form.errors:
        flash_errors(form)
    return redirect(reverse("index"))


@login_required
def del_position(request, portf_name: str, ticker: str) -> Response:
    """
    Deletes a specific ticker from a portfolio.

    Args:
        portf_name (str): The name of the portfolio from which the ticker should be deleted.
        ticker (str): The ticker symbol of the stock to be deleted from the portfolio.

    Returns:
        Response: Redirects the user to the portfolio index page.
    """
    ids = [
        item.id
        for item in Position.custom_obj.get_items(filters=(
            Q(portfolio_id__user_id=1) & # Change for user.id next
            Q(portfolio_id__name=portf_name) & 
            Q(ticker=ticker),
        ))
    ]
    if not ids:
        messages.add_message(
            request,
            messages.ERROR,
            f"An error occurred while trying to delete " + 
            f"the items of ticker '{ticker}' from portfolio '{portf_name}'."
        )
    else:
        Position.objects.filter(id__in_=ids).delete()
        messages.add_message(
            request,
            messages.SUCCESS,
            f"The items of ticker '{ticker}' have been deleted " + 
            f"from portfolio '{portf_name}'."
        )
    return redirect(reverse('index'))
