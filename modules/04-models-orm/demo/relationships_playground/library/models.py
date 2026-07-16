from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class AuthorProfile(models.Model):
    """One-to-one: each Author has exactly one profile, and each profile
    belongs to exactly one Author. Used to split rarely-needed data off the
    main model (here, just for demonstration) without a full FK/M2M."""

    author = models.OneToOneField(Author, on_delete=models.CASCADE, related_name="profile")
    biography = models.TextField(blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return f"Profile of {self.author.name}"


class Genre(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    # Many-to-one (ForeignKey): many Books, one Author.
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")
    # Many-to-many: a Book can belong to several Genres, a Genre has many Books.
    genres = models.ManyToManyField(Genre, related_name="books")

    def __str__(self):
        return self.title
