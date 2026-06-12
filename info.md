# Pinergy

Monitor your [Pinergy](https://www.pinergy.ie/) prepay electricity account from Home Assistant.

## Entities

- **Current balance** (€), **Days remaining**, **Last top-up amount** (€)
- **Today's**, **this week's**, and **this month's usage** (kWh) and **cost** (€)
- **Last meter reading** and **Last top-up** timestamps
- **Average home usage/cost today** comparisons with similar homes
- **Power**, **Emergency credit**, **Credit low**, and **Pending top-up** status

Daily usage history is imported into long-term statistics, ready to add to the **Energy Dashboard** (`Pinergy energy consumption` / `Pinergy energy cost`).

## Setup

After installing, add the integration via **Settings → Devices & Services → Add Integration → Pinergy** and sign in with your Pinergy app email and password. Data refreshes every 30 minutes.
