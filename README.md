# ScrapeNinja 🥷✈️

A robust American Airlines flight scraper that analyzes the value of award redemptions by calculating Cents Per Point (CPP) ratios. Built for reliability and stealth using advanced browser automation with support for both **CamouFox** (Firefox-based) and **Chromium** engines.

## Quick Start

`docker run anthonyfong/scraperninja:latest`

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation
```bash
# Install dependencies
uv sync

# Install browser automation engines
camoufox fetch    # Firefox-based (default, recommended)
# OR
playwright install chromium    # Alternative: Chromium support
```

### Basic Usage
```bash
# Analyze LAX → JFK flights for December 15, 2025 (using default CamouFox)
uv run main.py -o LAX -d JFK --date 2025-12-15 -p 1 -f logs/output.json

# With debug logging
uv run main.py -o LAX -d JFK --date 2025-12-15 -p 1 --debug

# Use Camoufox browser instead
uv run main.py -o LAX -d JFK --date 2025-12-15 -p 1 --use-camoufox
```

### Command Line Options
- `-o, --origin`: Origin airport code (e.g., LAX)
- `-d, --destination`: Destination airport code (e.g., JFK)
- `--date`: Flight date in YYYY-MM-DD format
- `-p, --passengers`: Number of passengers (default: 1)
- `-c, --cabin-class`: Cabin class - COACH, PREMIUM_ECONOMY, BUSINESS, FIRST (default: COACH)
- `-f, --output-file-path`: Output JSON file path (optional)
- `--debug`: Enable verbose debug logging
- `--direct-only`: Only consider direct flights
- `--use-camoufox`: Browser engine - camoufox, chromium (default: chromium)

## Docker Usage

### Build and Run with Docker
```bash
# Build the Docker image
docker build -t scraperninja .

# Run a single analysis output to stdout
docker run scraperninja
```

### Environment Configuration
Create a `.env` file for configuration:
```bash
# Optional proxy configuration
PROXY_URLS=http://username:password@proxy.example.com:8080,http://username:password@proxy.example.com:8081

# Other environment variables can be added here
```

## Overall Strategy

### Browser Engine Support

ScrapeNinja supports two powerful browser automation engines:

- **Chromium**: Alternative Playwright-based engine for environments where Firefox compatibility is needed
- **CamouFox**: Firefox-based engine with stealth capabilities and built-in anti-detection features

Choose your preferred engine during installation and runtime based on your specific requirements.

### 🎯 Core Philosophy

ScrapeNinja takes a **reliability-first approach** to flight data extraction by intercepting network requests rather than relying on fragile CSS selectors. This fundamental design choice makes the scraper significantly more robust against website UI changes.

### 🕵️ Scrapling Framework Advantages

Built on the powerful [Scrapling](https://github.com/D4Vinci/Scrapling) framework, which provides:

- **CamouFox Integration**: Uses Firefox-based CamouFox for superior stealth capabilities
- **Built-in Anti-Detection**: Randomized fingerprints, user agents, and behavioral patterns
- **Humanization**: Realistic delays, mouse movements, and interaction patterns
- **Geographic Randomization**: Random IP geolocation to avoid regional blocking
- **OS Fingerprint Spoofing**: Randomized operating system signatures

```python
self.session = StealthySession(
    page_action=self.network_spy.spy,
    humanize=True,           # Human-like behavior
    os_randomize=True,       # Randomize OS fingerprint
    google_search=True,      # Mimic Google search patterns  
    geoip=True,             # Random IP geolocation
    headless=True,          # Run without GUI
    proxy=proxy_url         # Optional proxy support
)
```

### 🌐 Network Request Interception
Instead of parsing HTML/CSS (which breaks when airlines update their UI), ScrapeNinja **spies on network traffic** to capture the actual API calls:

```python
class PageNetworkSpy:
    def spy(self, page: Page):
        page.on("request", self.__handle_request)
        page.on("response", self.__handle_response)
```

**Why This Works Better:**
- ✅ **Immune to UI changes** - API endpoints remain stable while CSS classes change frequently
- ✅ **Gets raw data** - Direct access to JSON responses, no HTML parsing needed  
- ✅ **More reliable** - Airlines can't easily obfuscate their own API calls
- ✅ **Future-proof** - Works even if they completely redesign the frontend

### 🔄 Retry Strategy with Exponential Backoff
Robust error handling ensures reliable data collection even under adverse conditions:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=5, max=60)
)
def __search_flight_details(self, search_url: str):
    # Flight search logic with automatic retries
```

**Retry Features:**
- **Exponential Backoff**: 5s → 10s → 20s → 40s delays between retries
- **Maximum Attempts**: Up to 3 retry attempts per request
- **Capped Wait Time**: Maximum 60-second delay to prevent infinite waits
- **Automatic Recovery**: Handles temporary network issues, rate limiting, and server errors

### 🌍 Optional Proxy Support
Environment-variable based proxy configuration for enhanced anonymity:

```bash
# Set proxy via environment variable
export PROXY_URL="http://username:password@proxy.example.com:8080"

# Or in .env file
PROXY_URL=http://username:password@proxy.example.com:8080
```

**Proxy Benefits:**
- **IP Rotation**: Avoid IP-based rate limiting
- **Geographic Flexibility**: Access region-specific pricing
- **Enhanced Anonymity**: Additional layer of obfuscation
- **Commercial Proxy Support**: Compatible with services like Oxylabs, Bright Data, etc.