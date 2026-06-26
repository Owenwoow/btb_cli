"""
interface/project.py — btb_cli 精简版

只保留抢票所需的 fetch_project_payload 函数（热门项目检测、预热）。
去掉了原项目中仅用于 Web UI 的 fetch_ticket_options、fetch_buyers 等函数。
"""
from __future__ import annotations

import copy
from typing import Any

NEW_PROJECT_DETAIL_URL = "https://mall.bilibili.com/mall-search-items/items_detail/info"
OLD_PROJECT_DETAIL_URL = "https://show.bilibili.com/api/ticket/project/getV2"


def _normalize_new_project_payload(
    new_payload: dict[str, Any], project_id: int
) -> dict[str, Any]:
    normalized_project_id = int(
        new_payload.get("projectId") or new_payload.get("itemsId") or project_id
    )
    raw_screens = new_payload.get("screenList")
    if not isinstance(raw_screens, list) or not raw_screens:
        raise RuntimeError("new project response missing screenList")

    screens = copy.deepcopy(raw_screens)
    screen_start_times = [
        int(screen.get("start_time", 0))
        for screen in screens
        if isinstance(screen, dict) and str(screen.get("start_time", 0)).isdigit()
    ]
    venue_info = copy.deepcopy(new_payload.get("skuVenueInfo") or {})
    if not isinstance(venue_info, dict):
        venue_info = {}
    venue_info.setdefault("name", "")
    venue_info.setdefault("address_detail", "")
    sales_dates = new_payload.get("salesDates")
    end_time = int(
        new_payload.get("endTime")
        or (max(screen_start_times) if screen_start_times else 0)
    )

    for screen in screens:
        if not isinstance(screen, dict):
            continue
        screen.setdefault("project_id", normalized_project_id)
        screen.setdefault("express_fee", 0)
        for ticket in screen.get("ticket_list", []):
            if not isinstance(ticket, dict):
                continue
            ticket.setdefault("project_id", normalized_project_id)
            ticket.setdefault("screen_name", screen.get("name", ""))
            sale_flag = ticket.get("sale_flag") or {}
            if isinstance(sale_flag, dict):
                ticket.setdefault("sale_flag_number", sale_flag.get("number"))

    return {
        "id": normalized_project_id,
        "name": new_payload.get("projectName", ""),
        "hotProject": bool(new_payload.get("hotProject", False)),
        "has_eticket": not any(
            int(screen.get("express_fee", 0) or 0) > 0
            for screen in screens
            if isinstance(screen, dict)
        ),
        "screen_list": screens,
        "sales_dates": copy.deepcopy(
            sales_dates if isinstance(sales_dates, list) else []
        ),
        "venue_info": venue_info,
        "start_time": min(screen_start_times) if screen_start_times else 0,
        "end_time": end_time,
    }


def _fetch_project_payload_new(*, request: Any, project_id: int) -> dict[str, Any]:
    request_headers = getattr(request, "headers", None)
    old_headers = {}
    if isinstance(request_headers, dict):
        old_headers = {
            "origin": request_headers.get("origin"),
            "referer": request_headers.get("referer"),
        }
        request_headers.update(
            {
                "origin": "https://mall.bilibili.com",
                "referer": (
                    "https://mall.bilibili.com/neul-next/ticket-renovation/detail.html"
                    "?id={0}&from=pc_ticketlist&noTitleBar=1".format(project_id)
                ),
            }
        )
    try:
        response = request.post(
            url=NEW_PROJECT_DETAIL_URL,
            data={
                "itemsId": project_id,
                "itemsDetailPageType": 3,
            },
            isJson=True,
        ).json()
    finally:
        if isinstance(request_headers, dict):
            for key, value in old_headers.items():
                if value is None:
                    request_headers.pop(key, None)
                else:
                    request_headers[key] = value

    errno = response.get("code", response.get("errno"))
    if response.get("success") is False or errno not in (None, 0):
        raise RuntimeError(
            response.get("message", response.get("msg", "failed to fetch new project"))
        )
    data = response.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("new project response data is empty")
    return _normalize_new_project_payload(data, project_id)


def _fetch_project_payload_old(*, request: Any, project_id: int) -> dict[str, Any]:
    response = request.get(
        url=(
            "{0}?version=134&id={1}&project_id={1}".format(
                OLD_PROJECT_DETAIL_URL,
                project_id,
            )
        )
    ).json()
    errno = response.get("errno", response.get("code"))
    if errno != 0:
        raise RuntimeError(
            response.get("msg", response.get("message", "failed to fetch project"))
        )
    data = response.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("old project response data is empty")
    return data


def fetch_project_payload(
    request: Any,
    project_id: int,
) -> dict[str, Any]:
    try:
        return _fetch_project_payload_new(request=request, project_id=project_id)
    except Exception as new_error:
        try:
            return _fetch_project_payload_old(request=request, project_id=project_id)
        except Exception as old_error:
            raise RuntimeError(
                "failed to fetch project detail from new and old APIs: "
                "new={0}; old={1}".format(new_error, old_error)
            ) from old_error
