# Cloudflare DNS Auto Updater

This python script is used to update DNS records on Cloudflare based on your public IP periodically.

No need for a static IP address!

## Copy `config_example.json` -> `config.json`

```json
{
	"zone_identifier": "00000000000000000000000000000000",
	"auth_email": "johndoe@example.com",
	"auth_key": "0000000000000000000000000000000000000",
	"ttl": 3600,
	"proxy": true,
	"records_to_sync": [
		"example.com",
		"subdomain.example.com"
	]
}
```

- **zone_identifier** - Click on your domain on the Cloudflare Dashboard. The Zone ID is on the right sidebar.
- **auth_email** - The one you use to login to Cloudflare.
- **auth_key** - The global API key you get from within your Cloudflare Profile.
- **ttl** - TTL (Time to live) in seconds.
- **proxy** - Whether the DNS record is proxied through Cloudflare.
- **records_to_sync** - An array of A-Records that should be updated according to your IP.
