export const formatCsvNumber = (value) => {
  if (value === null || value === undefined) {
    return ''
  }
  const numeric = Number(value)
  if (Number.isNaN(numeric)) {
    return ''
  }
  return numeric.toFixed(2)
}

export const escapeCsvValue = (value) => {
  if (value === null || value === undefined) {
    return ''
  }
  let stringValue = String(value)
  if (stringValue.includes('"')) {
    stringValue = stringValue.replace(/"/g, '""')
  }
  if (/[",\n]/.test(stringValue)) {
    return `"${stringValue}"`
  }
  return stringValue
}

export const buildCsvContent = (rows) =>
  rows
    .map((row) => row.map((cell) => escapeCsvValue(cell)).join(','))
    .join('\n')
