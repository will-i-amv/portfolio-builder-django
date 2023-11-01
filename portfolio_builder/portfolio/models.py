from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()
SIDES = (
    ('B', 'Buy'),
    ('S', 'Sell'),
)


class Security(models.Model):
    name = models.CharField(max_length=200)
    ticker = models.CharField(max_length=10, unique=True)
    exchange = models.CharField(max_length=10)
    currency = models.CharField(max_length=3, default='USD')
    country = models.CharField(max_length=3, default='USA')
    isin = models.CharField(max_length=12, default='')

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

    def __repr__(self) -> str:
        return (f"<Portfolio Name: {self.name}>")


class Position(models.Model):    
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

    def __repr__(self) -> str:
        return (
            f"<Ticker: {self.ticker}, " + 
            f"Quantity: {self.quantity}, " + 
            f"Price: {self.price}>"
        )
