from django.db import models
from django.contrib.auth.models import User


class CleaningMachine(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Area(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Street(models.Model):
    name = models.CharField(max_length=200)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='streets')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['name', 'area']
    
    def __str__(self):
        return f"{self.name} ({self.area.name})"


class WorkOrder(models.Model):
    street = models.ForeignKey(Street, on_delete=models.CASCADE)
    cleaning_machine = models.ForeignKey(CleaningMachine, on_delete=models.CASCADE)
    daily_passages = models.PositiveIntegerField()
    date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['street', 'cleaning_machine', 'date']
    
    def __str__(self):
        return f"{self.street.name} - {self.cleaning_machine.name} - {self.date}"


class PassagePlan(models.Model):
    cleaning_machine = models.ForeignKey(CleaningMachine, on_delete=models.CASCADE)
    day_of_month = models.PositiveIntegerField()
    required_passages = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    year = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['cleaning_machine', 'day_of_month', 'month', 'year']
        constraints = [
            models.CheckConstraint(check=models.Q(day_of_month__gte=1) & models.Q(day_of_month__lte=31), name='valid_day'),
            models.CheckConstraint(check=models.Q(month__gte=1) & models.Q(month__lte=12), name='valid_month'),
        ]
    
    def __str__(self):
        return f"{self.cleaning_machine.name} - {self.day_of_month}/{self.month}/{self.year} - {self.required_passages} passages"
