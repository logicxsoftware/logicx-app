import { readFileSync, writeFileSync } from 'node:fs'

const html = readFileSync('../logicx_app/public/frontend/index.html')
writeFileSync('../logicx_app/www/logicx_app.html', html)
