from __future__ import annotations

from django.forms.widgets import CheckboxInput, CheckboxSelectMultiple


class ToggleSwitchInput(CheckboxInput):
    """Render a boolean field using the slider-style toggle component."""

    template_name = "widgets/toggle_switch.html"

    def get_context(self, name, value, attrs):
        attrs = attrs or {}
        # Allow callers to pass the text that accompanies the toggle without
        # leaking a ``data-label`` attribute onto the rendered input element.
        label_text = attrs.pop("data-label", None)
        context = super().get_context(name, value, attrs)
        widget = context["widget"]
        widget_attrs = widget.setdefault("attrs", {})
        if label_text is None:
            label_text = widget_attrs.pop("data-label", None)
        widget["label_text"] = label_text
        return context


class ToggleCheckboxSelectMultiple(CheckboxSelectMultiple):
    """Render multiple choice checkboxes as stacked toggle switches."""

    template_name = "widgets/toggle_checkbox_select.html"

    # No additional context customisation is needed beyond the base widget.
