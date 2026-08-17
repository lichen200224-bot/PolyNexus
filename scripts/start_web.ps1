$ErrorActionPreference = "Stop"
Push-Location ".\apps\web"
try {
  npm run dev
} finally {
  Pop-Location
}
