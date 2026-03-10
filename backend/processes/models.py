from django.db import models


class AuthorisationProcess(models.Model):
	"""Parent model grouping questionnaires under a business authorisation process."""

	id = models.BigAutoField(primary_key=True)
	slug = models.SlugField(
		max_length=20,
		null=False,
		blank=False,
		unique=True,
		db_index=True,
		editable=True,
	)
	name = models.CharField(max_length=100, blank=False, null=False, editable=True)
	description = models.TextField(
		max_length=500,
		blank=False,
		null=False,
		editable=True,
	)
	sort_order = models.PositiveIntegerField(
		default=0,
		null=False,
		blank=False,
		db_index=True,
		help_text="Controls display order in UI; lower values appear first.",
	)
	created_at = models.DateTimeField(auto_now_add=True, editable=False)
	updated_at = models.DateTimeField(auto_now=True, editable=False)

	class Meta:
		ordering = ("sort_order",)

	def __str__(self):
		return f"[{self.slug}] {self.name}"
