import datetime as dt
from typing import Optional

from django import forms
from django.db.models import Case, F, FloatField, Q, Sum, When
from django.forms import (
    CharField, ChoiceField, DateField, DecimalField, IntegerField, 
    ValidationError
)

from portfolio_builder.portfolio.models import ( 
    Security, Portfolio, Position
)


def get_default_date(date_: Optional[dt.date] = None) -> dt.date:
    if date_ is None:
        date_ = dt.date.today()
    weekday = dt.date.isoweekday(date_)
    if weekday == 6: # Saturday
        date_ = date_ - dt.timedelta(days=1)
    elif weekday == 7: # Sunday
        date_ = date_ - dt.timedelta(days=2)
    return date_


def validate_date(date: DateField) -> None:
    input_trade_date = date
    try:
        day_of_week = dt.date.isoweekday(input_trade_date)
    except TypeError:
        raise ValidationError("The trade date format is invalid.")
    curr_date = get_default_date()
    if day_of_week == 6 or day_of_week == 7:
        raise ValidationError(
            "The trade date can't fall on weekends."
        )
    elif input_trade_date > curr_date:
        raise ValidationError(
            "The trade date can't be a date in the future."
        )


class AddPortfolioForm(forms.Form):
    name = CharField(
        label="New Portfolio", 
        min_length=3, 
        max_length=25
    )

    def clean_name(self) -> None:
        input_name = self.cleaned_data['name']
        portf_obj = Portfolio.custom_obj.get_first_item(
            filters=(
                Q(user_id=1) & # Change for user.id next
                Q(name=input_name),
            )
        )
        if portf_obj is not None:
            raise ValidationError(f"The portfolio '{input_name}' already exists.")
        return input_name


class SelectPortfolioForm(forms.Form):
    name = ChoiceField(
        label="Available Portfolios", 
        min_length=3, 
        max_length=25
    )

    def clean_name(self) -> None:
        input_name = self.cleaned_data['name']
        portf_obj = Portfolio.custom_obj.get_first_item(
            filters=(
                Q(user_id=1) & # Change for user.id next
                Q(name=input_name),
            )
        )
        if portf_obj is None:
            raise ValidationError(f"The portfolio '{input_name}' doesn't exist.")
        return input_name


class PositionForm(forms.Form):
    portfolio = forms.CharField(widget=forms.HiddenInput())
    ticker = CharField(
        label="Ticker",
        min_length=1,
        max_length=20,
    )
    quantity = IntegerField(
        "Quantity",
        min_value=1,
        max_value=100000,
    )
    price = DecimalField(
        "Price",
        min_value=1,
        max_value=1000000,
    )
    side = ChoiceField(
        "Side",
        choices=(('buy'), ('sell')),
    )
    trade_date = DateField(
        "Trade Date",
        initial=get_default_date, 
        validators=[validate_date],
    )
    comments = forms.CharField(widget=forms.Textarea, required=False)

    def clean_ticker(self) -> None:
        input_ticker = self.cleaned_data['ticker']
        ticker_obj = (
            Security
            .objects
            .filter(Q(ticker=input_ticker))
            .first()
        )
        if ticker_obj is None:
            raise ValidationError(
                f"The ticker '{input_ticker}' doesn't exist in the database."
            )
        return input_ticker
    
    def clean_side(self):
        raise NotImplementedError
    
    def clean_trade_date(self):
        raise NotImplementedError


class AddPositionForm(PositionForm):
    def clean_side(self) -> None:
        input_side = self.cleaned_data['side']
        if input_side == 'sell':
            raise ValidationError(f"You can't sell if your portfolio is empty.")
        return input_side
    
    def clean_trade_date(self) -> None:
        input_trade_date = self.cleaned_data['trade_date']
        return input_trade_date


class UpdatePositionForm(PositionForm):
    def clean_side(self) -> None:
        input_portfolio = self.cleaned_data['portfolio']
        input_side = self.cleaned_data['side']
        input_ticker = self.cleaned_data['ticker']
        input_price = self.cleaned_data['price']
        input_qty = self.cleaned_data['quantity']
        total_amount_sold = input_qty * input_price
        if input_side == 'sell':
            net_asset_values = [ 
                item.flows
                for item in Position.custom_obj.get_items(
                    filters=(
                        Q(portfolio_id__name=input_portfolio) &
                        Q(ticker=input_ticker)
                    ),
                    entities=[
                        Sum(Case(
                            When(side='buy', then=(F('quantity') * F('price'))),
                            When(side='sell', then=(F('quantity') * F('price') * (-1))),
                            output_field=FloatField()
                        )),
                    ]
                )
            ]
            net_asset_value = next(iter(net_asset_values), 0.0)
            if total_amount_sold > net_asset_value: 
                raise ValidationError(
                    f"You tried to sell USD {total_amount_sold} " + 
                    f"worth of '{input_ticker}', but you only have " + 
                    f"USD {net_asset_value} in total." 
                )
        return input_side

    def clean_trade_date(self) -> None:
        input_trade_date = self.cleaned_data['trade_date']
        input_ticker = self.cleaned_data['ticker']
        input_portfolio = self.cleaned_data['portfolio']
        position_obj = (
            Position.custom_obj.get_first_item(filters=(
                Q(portfolio_id__name=input_portfolio) &
                Q(ticker=input_ticker) &
                Q(is_last_trade=True)
            ))
        )
        if position_obj:
            last_trade_date = position_obj.trade_date
            if input_trade_date < last_trade_date:
                raise ValidationError(
                    f"The last trade date for ticker '{input_ticker}' " + 
                    f"is '{last_trade_date}', the new date can't be before that."
                )
        return input_trade_date
