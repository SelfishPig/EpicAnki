from html import escape

IMAGE_TOGGLE_SCRIPT = """
<script>
(() => {
  document.querySelectorAll(".main img").forEach((image) => {
    if (image.dataset.epicAnkiImageToggle === "true") {
      return;
    }

    image.dataset.epicAnkiImageToggle = "true";
    image.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      image.classList.toggle("epic-anki-image-expanded");
    });
  });
})();
</script>
"""


def build_incognito_question_template(main_field: str) -> str:
    main_field_tag = "{{cloze:" + main_field + "}}"
    return f"""
<div class="main">
  <div class="main-field">{main_field_tag}</div>
</div>
{IMAGE_TOGGLE_SCRIPT}
"""


def build_incognito_answer_template(
    main_field: str,
    extra_fields: list[str],
) -> str:
    main_field_tag = "{{cloze:" + main_field + "}}"
    sections = []

    for field_name in extra_fields:
        start_condition = "{{#" + field_name + "}}"
        end_condition = "{{/" + field_name + "}}"
        field_tag = "{{" + field_name + "}}"
        sections.append(
            f"""{start_condition}
  <div class="extra">
    <div class="extra-header">{escape(field_name)}</div>
    <div class="extra-content">{field_tag}</div>
  </div>
{end_condition}"""
        )

    extras_html = "\n\n".join(sections)
    divider_html = '<div class="divider"></div>' if sections else ""

    return f"""
<div class="main">
  <div class="main-field">{main_field_tag}</div>
  {divider_html}

{extras_html}
</div>
{IMAGE_TOGGLE_SCRIPT}
"""
