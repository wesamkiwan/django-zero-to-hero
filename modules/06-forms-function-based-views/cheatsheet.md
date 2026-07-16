# Cheat Sheet — Module 06: Forms & Function-Based Views (CRUD)

## ModelForm

```python
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "price", ...]      # always explicit, never "__all__"
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def clean_price(self):                    # single-field validation
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("...")
        return price

    def clean(self):                          # cross-field validation
        cleaned_data = super().clean()
        ...
        return cleaned_data
```

## CSRF

```django
<form method="post">
    {% csrf_token %}
    ...
</form>
```
Missing it on a POST form → Django rejects with 403. Always include it.

## The five-view CRUD pattern

```python
def x_list(request):
    qs = Model.objects.all()
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(name__icontains=q)
    return render(request, "app/x_list.html", {"objects": qs, "query": q})

def x_detail(request, pk):
    obj = get_object_or_404(Model, pk=pk)
    return render(request, "app/x_detail.html", {"object": obj})

def x_create(request):
    if request.method == "POST":
        form = XForm(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Created.")
            return redirect("app:x_detail", pk=obj.pk)
    else:
        form = XForm()
    return render(request, "app/x_form.html", {"form": form})

def x_update(request, pk):
    obj = get_object_or_404(Model, pk=pk)
    if request.method == "POST":
        form = XForm(request.POST, instance=obj)   # <- instance= makes it an UPDATE
        if form.is_valid():
            form.save()
            messages.success(request, "Updated.")
            return redirect("app:x_detail", pk=obj.pk)
    else:
        form = XForm(instance=obj)
    return render(request, "app/x_form.html", {"form": form})

def x_delete(request, pk):
    obj = get_object_or_404(Model, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Deleted.")
        return redirect("app:x_list")
    return render(request, "app/x_confirm_delete.html", {"object": obj})
```

## Post/Redirect/Get (PRG)

After a successful POST → always `redirect()` to a GET URL. Never
`render()` directly after a successful POST — that's what causes
"resubmit form?" browser warnings on refresh.

## Messages

```python
from django.contrib import messages
messages.success(request, "...")
messages.error(request, "...")
messages.warning(request, "...")
messages.info(request, "...")
```
```django
{% if messages %}
    {% for message in messages %}
        <p class="message-{{ message.tags }}">{{ message }}</p>
    {% endfor %}
{% endif %}
```

## Template form rendering

```django
<form method="post" class="model-form">
    {% csrf_token %}
    {{ form.non_field_errors }}
    {{ form.as_p }}          {# or render fields manually for full control #}
    <button type="submit">Save</button>
</form>
```

## Search via request.GET

```python
query = request.GET.get("q", "").strip()
if query:
    qs = qs.filter(name__icontains=query)
```
