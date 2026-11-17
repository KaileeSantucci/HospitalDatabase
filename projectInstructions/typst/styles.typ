// Reusable table styling and small table-building helpers.
#let report-table(headers, rows, caption, columns: auto, group-starts: (), font-size: 8.5pt, cell-inset: (x: 5pt, y: 4pt)) = {
  set text(size: font-size)
  let header-cells = headers.map(label => text(label, weight: "bold"))
  let body-cells = rows.flatten()
  figure(
    table(
      columns: columns,
      inset: cell-inset,
      align: left + top,
      fill: (x, y) => if y == 0 {
        rgb("#E3E8EE")
      } else if calc.even(y) {
        rgb("#F4F6F8")
      } else {
        white
      },
      stroke: (x, y) => if y == 0 {
        (bottom: 1pt + rgb("#AAB4C0"))
      } else if group-starts.contains(y - 1) {
        (top: 1.2pt + rgb("#8793A1"), bottom: 0.4pt + rgb("#D7DDE4"))
      } else {
        (bottom: 0.4pt + rgb("#D7DDE4"))
      },
      table.header(repeat: true, ..header-cells),
      ..body-cells,
    ),
    caption: caption,
  )
}

#let as-cell(value) = text(str(value))
#let raw-example(value) = raw("⟦" + value + "⟧")

#let sum-values(values) = values.fold(0, (total, value) => total + value)
