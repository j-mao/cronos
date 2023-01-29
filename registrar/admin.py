from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Course, CourseListing, Term, User


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    pass


class CourseListingInline(admin.TabularInline):
    model = CourseListing


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [CourseListingInline]


admin.site.register(User, UserAdmin)
