from django.contrib import admin
from .models import Note, NoteHistory, ShareLink, MediaFile


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'owner', 'creator_client_token', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('title', 'id', 'owner__username', 'creator_client_token')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('기본 정보', {
            'fields': ('id', 'title', 'content_json', 'status')
        }),
        ('소유자 정보', {
            'fields': ('owner', 'creator_client_token', 'creator_ip')
        }),
        ('보안', {
            'fields': ('edit_password_hash',)
        }),
        ('타임스탬프', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(NoteHistory)
class NoteHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'note', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('note__title', 'note__id')
    readonly_fields = ('id', 'created_at')
    fieldsets = (
        ('기본 정보', {
            'fields': ('id', 'note', 'created_at')
        }),
        ('변경 내용', {
            'fields': ('before_html', 'after_html', 'diff_html', 'editor_session_id')
        }),
    )


@admin.register(ShareLink)
class ShareLinkAdmin(admin.ModelAdmin):
    list_display = ('token', 'note', 'active', 'expires_at', 'created_at')
    list_filter = ('active', 'expires_at', 'created_at')
    search_fields = ('token', 'note__title', 'note__id')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('기본 정보', {
            'fields': ('token', 'note', 'active', 'expires_at')
        }),
        ('보안', {
            'fields': ('edit_password_hash',)
        }),
        ('타임스탬프', {
            'fields': ('created_at',)
        }),
    )


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'file_type', 'uploader', 'file_size', 'created_at')
    list_filter = ('file_type', 'created_at')
    search_fields = ('id', 'uploader__username', 'uploader_client_token')
    readonly_fields = ('id', 'created_at')
    fieldsets = (
        ('기본 정보', {
            'fields': ('id', 'file', 'file_type', 'mime_type', 'file_size')
        }),
        ('소유자 정보', {
            'fields': ('uploader', 'uploader_client_token')
        }),
        ('타임스탬프', {
            'fields': ('created_at',)
        }),
    )
