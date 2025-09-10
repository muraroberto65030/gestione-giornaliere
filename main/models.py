from django.db import models
from django.contrib.auth.models import User


class CleaningMachine(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    description = models.TextField(blank=True, verbose_name="Descrizione")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creato il")
    
    class Meta:
        verbose_name = "Macchina Spazzatrice"
        verbose_name_plural = "Macchine Spazzatrici"
    
    def __str__(self):
        return self.name


class Area(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    description = models.TextField(blank=True, verbose_name="Descrizione")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creata il")
    
    class Meta:
        verbose_name = "Area"
        verbose_name_plural = "Aree"
    
    def __str__(self):
        return self.name


class CleaningOperationType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    description = models.TextField(blank=True, verbose_name="Descrizione")
    frequency_per_week = models.PositiveIntegerField(default=1, verbose_name="Frequenza Settimanale")
    
    class Meta:
        verbose_name = "Tipo Operazione Pulizia"
        verbose_name_plural = "Tipi Operazioni Pulizia"
    
    def __str__(self):
        return self.name


class Street(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nome")
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='streets', verbose_name="Area")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creata il")
    
    class Meta:
        verbose_name = "Strada"
        verbose_name_plural = "Strade"
        unique_together = ['name', 'area']
    
    def __str__(self):
        return f"{self.name} ({self.area.name})"


class StreetCleaningOperation(models.Model):
    street = models.ForeignKey(Street, on_delete=models.CASCADE, related_name='operations', verbose_name="Strada")
    operation_type = models.ForeignKey(CleaningOperationType, on_delete=models.CASCADE, verbose_name="Tipo Operazione")
    day_of_month = models.PositiveIntegerField(verbose_name="Giorno del Mese")
    month = models.PositiveIntegerField(verbose_name="Mese")
    year = models.PositiveIntegerField(verbose_name="Anno")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creata il")
    
    class Meta:
        verbose_name = "Operazione Pulizia Strada"
        verbose_name_plural = "Operazioni Pulizia Strade"
        unique_together = ['street', 'operation_type', 'day_of_month', 'month', 'year']
        constraints = [
            models.CheckConstraint(check=models.Q(day_of_month__gte=1) & models.Q(day_of_month__lte=31), name='valid_operation_day'),
            models.CheckConstraint(check=models.Q(month__gte=1) & models.Q(month__lte=12), name='valid_operation_month'),
        ]
    
    def __str__(self):
        return f"{self.street.name} - {self.operation_type.name} - {self.day_of_month}/{self.month}/{self.year}"


class WorkOrder(models.Model):
    street = models.ForeignKey(Street, on_delete=models.CASCADE, verbose_name="Strada")
    cleaning_machine = models.ForeignKey(CleaningMachine, on_delete=models.CASCADE, verbose_name="Macchina Spazzatrice")
    daily_passages = models.PositiveIntegerField(verbose_name="Passaggi Giornalieri")
    date = models.DateField(verbose_name="Data")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Creato da")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creato il")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Aggiornato il")
    
    class Meta:
        verbose_name = "Ordine di Lavoro"
        verbose_name_plural = "Ordini di Lavoro"
        unique_together = ['street', 'cleaning_machine', 'date']
    
    def __str__(self):
        return f"{self.street.name} - {self.cleaning_machine.name} - {self.date}"


class PassagePlan(models.Model):
    cleaning_machine = models.ForeignKey(CleaningMachine, on_delete=models.CASCADE, verbose_name="Macchina Spazzatrice")
    day_of_month = models.PositiveIntegerField(verbose_name="Giorno del Mese")
    required_passages = models.PositiveIntegerField(verbose_name="Passaggi Richiesti")
    month = models.PositiveIntegerField(verbose_name="Mese")
    year = models.PositiveIntegerField(verbose_name="Anno")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creato il")
    
    class Meta:
        verbose_name = "Piano Passaggi"
        verbose_name_plural = "Piani Passaggi"
        unique_together = ['cleaning_machine', 'day_of_month', 'month', 'year']
        constraints = [
            models.CheckConstraint(check=models.Q(day_of_month__gte=1) & models.Q(day_of_month__lte=31), name='valid_day'),
            models.CheckConstraint(check=models.Q(month__gte=1) & models.Q(month__lte=12), name='valid_month'),
        ]
    
    def __str__(self):
        return f"{self.cleaning_machine.name} - {self.day_of_month}/{self.month}/{self.year} - {self.required_passages} passaggi"
