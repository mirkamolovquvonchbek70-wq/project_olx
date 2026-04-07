import django_filters
from django import forms
from django.db.models import Q, IntegerField
from django.db.models.functions import Cast
from django.db.models.fields.json import KeyTextTransform

from apps.models import Announcement


INPUT_CLASS = "w-full bg-white border-b-2 border-gray-300 px-4 py-3 outline-none focus:border-[#002f34]"
SELECT_CLASS = "w-full bg-white border-b-2 border-gray-300 px-4 py-3 outline-none focus:border-[#002f34]"


class AnnouncementFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method="filter_q",
        label="Поиск"
    )
    min_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="gte",
        label="Цена от"
    )
    max_price = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="lte",
        label="Цена до"
    )

    class Meta:
        model = Announcement
        fields = []

    def __init__(self, *args, category=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.category = category
        self.dynamic_fields = []
        self.dynamic_config = {}

        self.filters["q"].field.widget = forms.TextInput(attrs={
            "class": INPUT_CLASS,
            "placeholder": "Что ищете?",
        })
        self.filters["min_price"].field.widget = forms.NumberInput(attrs={
            "class": INPUT_CLASS,
            "placeholder": "От:",
        })
        self.filters["max_price"].field.widget = forms.NumberInput(attrs={
            "class": INPUT_CLASS,
            "placeholder": "До:",
        })

        if self.category:
            children = self.category.get_children()
            if children.exists():
                self.filters['ichki_toifa'] = django_filters.ModelChoiceFilter(
                    queryset=children,
                    method='filter_subcategory',
                    label="Ichki toifa",
                    empty_label="Hamma e'lonlar",
                    widget=forms.Select(attrs={
                        "class": SELECT_CLASS,
                    })
                )

        schema = self.get_category_schema(category)

        for item in schema:
            field_name = item.get("name")
            field_type = item.get("type")
            label = item.get("label", field_name)
            options = item.get("options") or []

            if not field_name or not field_type:
                continue

            if field_type == "int":
                min_name = f"{field_name}_min"
                max_name = f"{field_name}_max"

                self.dynamic_config[min_name] = {
                    "source_name": field_name,
                    "mode": "min",
                    "type": "int",
                }
                self.dynamic_config[max_name] = {
                    "source_name": field_name,
                    "mode": "max",
                    "type": "int",
                }

                min_filter = django_filters.NumberFilter(
                    field_name=min_name,
                    method="filter_dynamic_int",
                    label=f"{label} от",
                    widget=forms.NumberInput(attrs={
                        "class": INPUT_CLASS,
                        "placeholder": "От:",
                    }),
                )
                min_filter.parent = self
                self.filters[min_name] = min_filter

                max_filter = django_filters.NumberFilter(
                    field_name=max_name,
                    method="filter_dynamic_int",
                    label=f"{label} до",
                    widget=forms.NumberInput(attrs={
                        "class": INPUT_CLASS,
                        "placeholder": "До:",
                    }),
                )
                max_filter.parent = self
                self.filters[max_name] = max_filter

                self.dynamic_fields.append({
                    "type": "range",
                    "label": label,
                    "min_name": min_name,
                    "max_name": max_name,
                })

            elif field_type == "select":
                choice_filter = django_filters.ChoiceFilter(
                    field_name=field_name,
                    choices=[("", "Все объявления")] + [(x, x) for x in options],
                    method="filter_dynamic_choice",
                    label=label,
                    widget=forms.Select(attrs={
                        "class": SELECT_CLASS,
                    }),
                )
                choice_filter.parent = self
                self.filters[field_name] = choice_filter

                self.dynamic_config[field_name] = {
                    "source_name": field_name,
                    "type": "select",
                }

                self.dynamic_fields.append({
                    "type": "select",
                    "label": label,
                    "name": field_name,
                })

            elif field_type == "multiselect":
                multi_filter = django_filters.MultipleChoiceFilter(
                    field_name=field_name,
                    choices=[(x, x) for x in options],
                    method="filter_dynamic_multi",
                    label=label,
                    widget=forms.SelectMultiple(attrs={
                        "class": SELECT_CLASS,
                    }),
                )
                multi_filter.parent = self
                self.filters[field_name] = multi_filter

                self.dynamic_config[field_name] = {
                    "source_name": field_name,
                    "type": "multiselect",
                }

                self.dynamic_fields.append({
                    "type": "multiselect",
                    "label": label,
                    "name": field_name,
                })

        order = ["q", "min_price", "max_price"]
        for item in self.dynamic_fields:
            if item["type"] == "range":
                order.extend([item["min_name"], item["max_name"]])
            else:
                order.append(item["name"])


        order = ["q", "min_price", "max_price"]

        # Обязательно добавляем ichki_toifa в order_fields, чтобы форма не выдавала ошибку
        # --- ОБНОВЛЕННЫЙ БЛОК: Ichki toifa ---
        if self.category:
            # 1. Определяем, какие категории показывать в выпадающем списке
            if self.category.get_children().exists():
                # Мы в главной (например, Yengil avtomashinalar). Показываем её детей.
                dropdown_queryset = self.category.get_children()
                initial_val = None
            elif self.category.parent:
                # Мы в подкатегории (например, Chevrolet). Показываем детей её родителя (соседние марки).
                dropdown_queryset = self.category.parent.get_children()
                initial_val = self.category  # Чтобы Chevrolet был сразу выбран в списке
            else:
                dropdown_queryset = None

            # 2. Если есть что показывать, создаем поле
            if dropdown_queryset is not None:
                self.filters['ichki_toifa'] = django_filters.ModelChoiceFilter(
                    queryset=dropdown_queryset,
                    method='filter_subcategory',
                    to_field_name='slug',
                    label="Ichki toifa",
                    empty_label="Hamma e'lonlar",
                    widget=forms.Select(attrs={
                        "class": SELECT_CLASS,
                        "id": "ichki-toifa-select",
                    })
                )

                # Делаем текущую подкатегорию выбранной по умолчанию
                if initial_val:
                    self.filters['ichki_toifa'].extra['initial'] = initial_val
        # -------------------------------------

        for item in self.dynamic_fields:
            if item["type"] == "range":
                order.extend([item["min_name"], item["max_name"]])
            else:
                order.append(item["name"])

        self.form.order_fields(order)

        # --- НОВОЕ: Метод для фильтрации по выбранной подкатегории ---

    def filter_subcategory(self, queryset, name, value):
        if value:
            # Получаем саму подкатегорию и все её дочерние узлы (если уровень вложенности > 2)
            categories = value.get_descendants(include_self=True)
            return queryset.filter(category__in=categories)
        return queryset

    def get_category_schema(self, category):
        if not category:
            return []

        if category.attribute:
            return category.attribute

        parent = category.parent
        while parent:
            if parent.attribute:
                return parent.attribute
            parent = parent.parent

        for child in category.get_descendants():
            if child.attribute:
                return child.attribute

        return []

    def filter_q(self, queryset, name, value):
        if not value:
            return queryset

        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )

    def filter_dynamic_choice(self, queryset, name, value):
        if value in (None, ""):
            return queryset

        config = self.dynamic_config.get(name)
        if not config:
            return queryset

        source_name = config["source_name"]
        return queryset.filter(**{f"attribute__{source_name}": value})

    def filter_dynamic_multi(self, queryset, name, value):
        if not value:
            return queryset

        config = self.dynamic_config.get(name)
        if not config:
            return queryset

        source_name = config["source_name"]
        q = Q()

        for item in value:
            q |= Q(**{f"attribute__{source_name}__contains": [item]})

        return queryset.filter(q)

    def filter_dynamic_int(self, queryset, name, value):
        if value in (None, ""):
            return queryset

        config = self.dynamic_config.get(name)
        if not config:
            return queryset

        source_name = config["source_name"]
        mode = config["mode"]
        alias = f"attr_{source_name}"

        queryset = queryset.annotate(
            **{
                alias: Cast(
                    KeyTextTransform(source_name, "attribute"),
                    IntegerField()
                )
            }
        )

        if mode == "min":
            return queryset.filter(**{f"{alias}__gte": value})
        return queryset.filter(**{f"{alias}__lte": value})