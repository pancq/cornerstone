export function exportToCSV<T>(data: T[], headers: Record<keyof T, string>, filename: string): void {
  const keys = Object.keys(headers) as (keyof T)[]
  const csvContent = [
    keys.map((key) => `"${headers[key]}"`).join(','),
    ...data.map((row) =>
      keys.map((key) => {
        const value = row[key]
        const escaped = String(value ?? '').replace(/"/g, '""')
        return `"${escaped}"`
      }).join(',')
    ),
  ].join('\n')

  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

export function parseCSV(csvText: string): string[][] {
  const lines = csvText.split('\n').filter((line) => line.trim())
  const result: string[][] = []
  
  for (const line of lines) {
    const values: string[] = []
    let current = ''
    let inQuotes = false
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i]
      const nextChar = line[i + 1]
      
      if (char === '"' && nextChar === '"') {
        current += '"'
        i++
      } else if (char === '"') {
        inQuotes = !inQuotes
      } else if (char === ',' && !inQuotes) {
        values.push(current)
        current = ''
      } else {
        current += char
      }
    }
    values.push(current)
    result.push(values)
  }
  
  return result
}
