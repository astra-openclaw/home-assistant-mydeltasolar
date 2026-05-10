"""Config flow for MyDeltaSolar."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import MyDeltaSolarAuthError, MyDeltaSolarClient, MyDeltaSolarError
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES, DOMAIN


class MyDeltaSolarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a MyDeltaSolar config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
            self._abort_if_unique_id_configured()

            session = async_create_clientsession(self.hass)
            client = MyDeltaSolarClient(
                session, user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            try:
                await client.async_login()
            except MyDeltaSolarAuthError:
                errors["base"] = "invalid_auth"
            except MyDeltaSolarError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                    options={
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL_MINUTES
                    ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                }
            ),
            errors=errors,
        )
