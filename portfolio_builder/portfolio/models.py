from typing import List, Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Case, F, FloatField, Q, QuerySet, Sum, When


User = get_user_model()


class SecurityMgr(models.Manager):
    def get_items(
        self,
        filters: Q,
        entities: Optional[List[str]] = None,
        orderby: Optional[List[str]] = None,
    ) -> QuerySet:
        if not entities:
            entities = [
                'name',
                'ticker',
                'exchange',
                'currency',
                'country',
                'isin',
            ]
        if not orderby:
            orderby = ['ticker']
        items = (
            self
            .get_queryset()
            .filter(filters)
            .order_by(*orderby)
            .values(*entities)
            .all()
        )
        return items


class PriceMgr(models.Manager):
    def get_items(
        self,
        filters: Q,
        entities: Optional[List[str]] = None,
        orderby: Optional[List[str]] = None,
    ) -> QuerySet:
        if not entities:
            entities = ['date', 'close']
        if not orderby:
            orderby = ['date'] 
        prices = (
            self
            .get_queryset()
            .select_related('ticker_id')
            .filter(filters)
            .order_by(*orderby)
            .values(*entities)
            .all()
        )
        return prices


class PortfolioMgr(models.Manager):
    def _base_query(self, filters: Q) -> QuerySet:
        query = (
            self
            .get_queryset()
            .filter(filters)
        )
        return query

    def get_first_item(self, filters: Q) -> Optional['Portfolio']:
        item = self._base_query(filters).first()
        return item

    def get_items(
        self,
        filters: Q,
        entities: Optional[List[str]] = None,
        orderby: Optional[List[str]] = None,
    ) -> QuerySet:
        if not entities: 
            entities = ['name']
        if not orderby: 
            orderby = ['id']
        items = (
            self
            ._base_query(filters)
            .order_by(*orderby)
            .values(*entities)
            .all()
        )
        return items


class PositionMgr(models.Manager):
    def _base_query(self, filters: Q) -> QuerySet:
        query = (
            self
            .get_queryset()
            .select_related('portfolio_id')
            .filter(filters)
        )
        return query

    def get_first_item(self, filters: Q) -> Optional['Position']:
        item = self._base_query(filters).first()
        return item

    def get_items(
        self,
        filters: Q,
        entities: Optional[List[str]] = None,
        orderby: Optional[List[str]] = None,
    ) -> QuerySet:
        if not entities: 
            entities = [
                'id',
                'ticker',
                'quantity',
                'price',
                'side',
                'trade_date',
                'comments',
            ]
        if not orderby: 
            orderby = ['id']
        items = (
            self
            ._base_query(filters)
            .order_by(*orderby)
            .values(*entities)
            .all()
        )
        return items

    def get_grouped_items(self, filters: Q) -> QuerySet:
        items = (
            self
            ._base_query(filters)
            .values('trade_date')
            .annotate(
                flows=Sum(
                    Case(
                        When(side='buy', then=(F('quantity') * F('price'))),
                        When(side='sell', then=(F('quantity') * F('price') * (-1))),
                        output_field=FloatField()
                    )
                )
            )
            .order_by('trade_date')
        )
        return items


class Security(models.Model):
    name = models.CharField(max_length=200)
    ticker = models.CharField(max_length=10, unique=True)
    exchange = models.CharField(max_length=10)
    currency = models.CharField(max_length=3, default='USD')
    country = models.CharField(max_length=3, default='USA')
    isin = models.CharField(max_length=12, default='')
    custom_obj = SecurityMgr()

    def __repr__(self) -> str:
        return (
            f"<Name: {self.name}, " + 
            f"Ticker: {self.ticker}>"
        )


class Price(models.Model):
    date = models.DateField()
    close = models.DecimalField(max_digits=12, decimal_places=6)
    ticker_id = models.ForeignKey(
        'Security', 
        on_delete=models.CASCADE, 
        related_name='ticker_id',
    )
    custom_obj = PriceMgr()

    class Meta:
        indexes = [
            models.Index(fields=['date', 'ticker_id'], name='idx_date_tickerid'),
            models.Index(fields=['ticker_id', 'date'], name='idx_tickerid_date'),
        ]
    
    def __repr__(self) -> str:
        return (
            f"<Date: {self.date}, " + 
            f"Close Price: {self.close}, " + 
            f"Ticker ID: {self.ticker_id}>"
        )



class Portfolio(models.Model):
    name = models.CharField(max_length=25)
    user_id = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='user_id',
    )
    custom_obj = PortfolioMgr()

    def __repr__(self) -> str:
        return (f"<Portfolio Name: {self.name}>")


class Position(models.Model):
    SIDES = (
        ('B', 'Buy'),
        ('S', 'Sell'),
    )
    ticker = models.CharField(max_length=20, unique=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=6)
    side = models.CharField(max_length=1, choices=SIDES)
    trade_date = models.DateField()
    is_last_trade = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    comments = models.CharField(max_length=140)
    portfolio_id = models.ForeignKey(
        'Portfolio', 
        on_delete=models.CASCADE,
        related_name='portfolio_id',
    )
    custom_obj = PositionMgr()

    def __repr__(self) -> str:
        return (
            f"<Ticker: {self.ticker}, " + 
            f"Quantity: {self.quantity}, " + 
            f"Price: {self.price}>"
        )
