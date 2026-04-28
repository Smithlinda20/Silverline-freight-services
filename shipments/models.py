import secrets
import string
from datetime import timedelta

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class ShipmentOrder(models.Model):
    class ShipmentStatus(models.TextChoices):
        PENDING = "pending", "Pending Pickup"
        IN_TRANSIT = "in_transit", "In Transit"
        ON_HOLD = "on_hold", "On Hold"
        DELIVERED = "delivered", "Delivered"

    class NoticeOption(models.TextChoices):
        DEFAULT_NOTICE = "default_notice", "Option 1 - Processing Charges Notice"
        ORDER_CHARGES = "order_charges", "Option 2 - Order Charges Notice"

    tracking_number = models.CharField(max_length=14, unique=True, editable=False, db_index=True)
    from_address = models.TextField()
    to_address = models.TextField()
    item_name = models.CharField(max_length=180, default="General Cargo")
    item_description = models.TextField(blank=True)
    item_quantity = models.PositiveIntegerField(default=1)
    item_weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    sender_name = models.CharField(max_length=140, blank=True)
    receiver_name = models.CharField(max_length=140, blank=True)
    current_location = models.CharField(max_length=180, blank=True, default="Processing Hub")
    progress_percent = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    status = models.CharField(
        max_length=24,
        choices=ShipmentStatus.choices,
        default=ShipmentStatus.PENDING,
    )
    route_waypoints = models.TextField(
        blank=True,
        default="",
        help_text="Optional intermediate stops, one per line.",
    )
    current_waypoint_index = models.PositiveSmallIntegerField(default=0)
    auto_update_enabled = models.BooleanField(default=False)
    auto_update_percent_step = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    auto_update_interval_minutes = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(1)],
    )
    auto_update_last_run = models.DateTimeField(null=True, blank=True)
    client_notice_option = models.CharField(
        max_length=24,
        choices=NoticeOption.choices,
        default=NoticeOption.DEFAULT_NOTICE,
    )
    hold_active = models.BooleanField(default=False)
    hold_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    hold_reason = models.TextField(blank=True)
    hold_message = models.TextField(
        blank=True,
        default=(
            "Your order is currently on hold due to certain applicable charges. Kindly proceed with the "
            "payment to resume processing. Please note that this charge is fully refundable."
        ),
    )
    expected_delivery_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tracking_number} - {self.get_status_display()}"

    @staticmethod
    def _build_tracking_number():
        alphabet = string.ascii_uppercase + string.digits
        suffix = "".join(secrets.choice(alphabet) for _ in range(10))
        return f"SLF{suffix}"

    def get_route_points(self):
        points = []
        if self.from_address:
            points.append(self.from_address.strip())
        for line in (self.route_waypoints or "").splitlines():
            stop = line.strip()
            if stop and (not points or points[-1] != stop):
                points.append(stop)
        if self.to_address:
            destination = self.to_address.strip()
            if not points or points[-1] != destination:
                points.append(destination)
        return points

    def apply_auto_progress(self, now=None):
        if not self.auto_update_enabled or self.hold_active:
            return False
        if self.status == self.ShipmentStatus.DELIVERED or self.progress_percent >= 100:
            self.auto_update_enabled = False
            self.save(update_fields=["auto_update_enabled"])
            return False

        now = now or timezone.now()
        if self.auto_update_last_run is None:
            self.auto_update_last_run = now
            self.save(update_fields=["auto_update_last_run"])
            return False

        interval = max(int(self.auto_update_interval_minutes or 1), 1)
        elapsed_seconds = (now - self.auto_update_last_run).total_seconds()
        steps = int(elapsed_seconds // (interval * 60))
        if steps <= 0:
            return False

        route_points = self.get_route_points()
        if route_points:
            self.current_waypoint_index = min(
                self.current_waypoint_index + steps,
                len(route_points) - 1,
            )
            self.current_location = route_points[self.current_waypoint_index]

        self.progress_percent = min(
            100,
            self.progress_percent + (steps * int(self.auto_update_percent_step or 1)),
        )

        if self.progress_percent >= 100:
            self.progress_percent = 100
            self.status = self.ShipmentStatus.DELIVERED
            self.auto_update_enabled = False
            if route_points:
                self.current_waypoint_index = len(route_points) - 1
                self.current_location = route_points[-1]
            elif self.to_address:
                self.current_location = self.to_address
        elif self.status == self.ShipmentStatus.PENDING:
            self.status = self.ShipmentStatus.IN_TRANSIT

        self.auto_update_last_run = self.auto_update_last_run + timedelta(minutes=steps * interval)
        self.save(
            update_fields=[
                "current_waypoint_index",
                "current_location",
                "progress_percent",
                "status",
                "auto_update_enabled",
                "auto_update_last_run",
            ]
        )
        return True

    def save(self, *args, **kwargs):
        if not self.tracking_number:
            candidate = self._build_tracking_number()
            while ShipmentOrder.objects.filter(tracking_number=candidate).exists():
                candidate = self._build_tracking_number()
            self.tracking_number = candidate

        route_points = self.get_route_points()
        if route_points:
            if self.current_waypoint_index >= len(route_points):
                self.current_waypoint_index = len(route_points) - 1
            if not self.current_location:
                self.current_location = route_points[self.current_waypoint_index]
        else:
            self.current_waypoint_index = 0

        if self.progress_percent > 100:
            self.progress_percent = 100
        if self.status == self.ShipmentStatus.DELIVERED and self.progress_percent < 100:
            self.progress_percent = 100

        if self.auto_update_enabled and self.auto_update_last_run is None:
            self.auto_update_last_run = timezone.now()

        if self.hold_active:
            self.status = self.ShipmentStatus.ON_HOLD
            if not self.hold_message:
                self.hold_message = (
                    "Your order is currently on hold due to certain applicable charges. Kindly proceed with the "
                    "payment to resume processing. Please note that this charge is fully refundable."
                )
        else:
            self.hold_amount = None
            self.hold_reason = ""
            self.hold_message = ""
        super().save(*args, **kwargs)

    def place_on_hold(self, amount, reason, message=None):
        self.hold_active = True
        self.hold_amount = amount
        self.hold_reason = reason
        self.hold_message = message or self.hold_message
        self.status = self.ShipmentStatus.ON_HOLD
        self.save(update_fields=["hold_active", "hold_amount", "hold_reason", "hold_message", "status"])

    def release_hold(self):
        self.hold_active = False
        self.status = (
            self.ShipmentStatus.DELIVERED
            if self.progress_percent >= 100
            else self.ShipmentStatus.IN_TRANSIT
        )
        self.hold_amount = None
        self.hold_reason = ""
        self.hold_message = ""
        self.save(
            update_fields=[
                "hold_active",
                "status",
                "hold_amount",
                "hold_reason",
                "hold_message",
            ]
        )
