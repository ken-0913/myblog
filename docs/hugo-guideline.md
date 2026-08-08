# Details shortcode



## **Example**

With this Markdown:

```text
{{< details summary="See the details" >}}
This is a **bold** word.
{{< /details >}}
```

Hugo renders this HTML:

```go-html-template
<details>
  <summary>See the details</summary>
  <p>This is a <strong>bold</strong> word.</p>
</details>
```

Which looks like this in your browser:

This is a **bold** word.



## **Arguments**

`summary`

(`string`) The content of the child `summary` element rendered from Markdown to HTML. Default is `Details`.

`open`

(`bool`) Whether to initially display the content of the `details` element. Default is `false`.

`class`

(`string`) The `class` attribute of the `details` element.

`name`

(`string`) The `name` attribute of the `details` element.

`title`

(`string`) The `title` attribute of the `details` element.

## **Styling**

Use CSS to style the `details` element, the `summary` element, and the content itself.

```css
/* target the details element */
details { }

/* target the summary element */
details > summary { }

/* target the children of the summary element */
details > summary > * { }

/* target the content */
details > :not(summary) { }
```

