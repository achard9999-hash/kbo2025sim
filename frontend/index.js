const Streamlit = window.StreamlitComponentBase || window.Streamlit;

function h(tag, props, ...children) {
  const el = document.createElement(tag);

  if (props) {
    Object.entries(props).forEach(([key, value]) => {
      if (key === "className") el.className = value;
      else if (key === "style" && value && typeof value === "object") {
        Object.assign(el.style, value);
      } else if (key.startsWith("on") && typeof value === "function") {
        el.addEventListener(key.slice(2).toLowerCase(), value);
      } else if (value !== false && value != null) {
        el.setAttribute(key, String(value));
      }
    });
  }

  children.flat().forEach((child) => {
    if (child == null) return;
    if (typeof child === "string" || typeof child === "number") {
      el.appendChild(document.createTextNode(String(child)));
    } else {
      el.appendChild(child);
    }
  });

  return el;
}

function emitAction(type, payload = {}) {
  const value = {
    type,
    payload,
    nonce: Date.now(),
  };
  Streamlit.setComponentValue(value);
}

function card(title, bodyNode) {
  return h(
    "div",
    {
      style: {
        background: "#fff",
        border: "2px solid #cbd5e1",
        borderRadius: "18px",
        padding: "14px",
        boxShadow: "0 8px 18px rgba(15,23,42,0.06)",
        marginBottom: "12px",
      },
    },
    h(
      "div",
      {
        style: {
          fontWeight: "900",
          fontSize: "16px",
          marginBottom: "10px",
          color: "#0f172a",
        },
      },
      title
    ),
    bodyNode
  );
}

function chip(text) {
  return h(
    "span",
    {
      style: {
        display: "inline-block",
        borderRadius: "999px",
        padding: "6px 10px",
        fontSize: "12px",
        fontWeight: "900",
        background: "#f8fafc",
        color: "#0f172a",
        border: "1px solid #cbd5e1",
        marginRight: "6px",
        marginBottom: "6px",
      },
    },
    text
  );
}

function actionButton(label, onClick, disabled = false) {
  return h(
    "button",
    {
      onClick,
      disabled,
      style: {
        width: "100%",
        minHeight: "42px",
        borderRadius: "12px",
        border: "1px solid #94a3b8",
        background: disabled ? "#e2e8f0" : "#ffffff",
        color: "#0f172a",
        fontWeight: "800",
        cursor: disabled ? "not-allowed" : "pointer",
      },
    },
    label
  );
}

function renderDashboard(payload) {
  const root = document.getElementById("root");
  root.innerHTML = "";

  const appPayload = payload?.appPayload || {};
  const live = appPayload.live_game || {};
  const game = live.game_state || null;
  const manager = live.manager_actions || {};

  const wrap = h("div", {
    style: {
      padding: "8px",
      background: "transparent",
    },
  });

  if (!live.has_live_game || !game) {
    wrap.appendChild(
      card(
        "라이브 경기 상태",
        h(
          "div",
          {
            style: {
              color: "#475569",
              fontWeight: "700",
            },
          },
          "아직 시작한 한화 경기가 없습니다. 상단 탭에서 경기 시작 후 다시 보세요."
        )
      )
    );
    root.appendChild(wrap);
    Streamlit.setFrameHeight(document.body.scrollHeight);
    return;
  }

  const scoreWrap = h(
    "div",
    {
      style: {
        background: "linear-gradient(180deg, #64748b 0%, #64748b 12%, #334155 12%, #334155 100%)",
        borderRadius: "24px",
        border: "3px solid #1e293b",
        boxShadow: "0 12px 0 #334155, 0 18px 28px rgba(15,23,42,0.18)",
        padding: "14px",
        color: "white",
        marginBottom: "14px",
      },
    },
    h(
      "div",
      {
        style: {
          display: "grid",
          gridTemplateColumns: "1fr auto 1fr",
          gap: "12px",
          alignItems: "center",
          marginBottom: "14px",
        },
      },
      h(
        "div",
        {
          style: {
            background: "rgba(255,255,255,0.10)",
            border: "2px solid rgba(255,255,255,0.18)",
            borderRadius: "18px",
            padding: "12px 14px",
          },
        },
        h("div", { style: { fontSize: "12px", fontWeight: "800", color: "#cbd5e1" } }, "AWAY"),
        h("div", { style: { fontSize: "24px", fontWeight: "900" } }, game.away_team)
      ),
      h(
        "div",
        {
          style: {
            fontSize: "42px",
            fontWeight: "900",
            lineHeight: "1",
            textAlign: "center",
            minWidth: "100px",
          },
        },
        `${game.score.away} : ${game.score.home}`
      ),
      h(
        "div",
        {
          style: {
            background: "rgba(255,255,255,0.10)",
            border: "2px solid rgba(255,255,255,0.18)",
            borderRadius: "18px",
            padding: "12px 14px",
            textAlign: "right",
          },
        },
        h("div", { style: { fontSize: "12px", fontWeight: "800", color: "#cbd5e1" } }, "HOME"),
        h("div", { style: { fontSize: "24px", fontWeight: "900" } }, game.home_team)
      )
    ),
    h(
      "div",
      null,
      chip(`${game.inning}회 ${game.half_kor}`),
      chip(`${game.outs}아웃`),
      chip(game.bases_text),
      chip(`공격 ${game.offense_team}`),
      chip(`수비 ${game.defense_team}`)
    )
  );

  wrap.appendChild(scoreWrap);

  const grid = h("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1.05fr 0.95fr",
      gap: "12px",
    },
  });

  const currentBatter = game.current_batter || {};
  const currentPitcher = game.current_pitcher || {};

  const stateCard = card(
    "현재 경기 상태",
    h(
      "div",
      null,
      infoRow("공격 팀", game.offense_team),
      infoRow("수비 팀", game.defense_team),
      infoRow("다음 타자", currentBatter.name || "-"),
      infoRow("현재 투수", `${currentPitcher.name || "-"}${currentPitcher.role ? ` (${currentPitcher.role})` : ""}`),
      h(
        "div",
        {
          style: {
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            gap: "8px",
            marginTop: "12px",
          },
        },
        actionButton("1타석 진행", () => emitAction("live_pa")),
        actionButton("반이닝 진행", () => emitAction("live_half")),
        actionButton("경기 끝까지 진행", () => emitAction("simulate_selected"))
      )
    )
  );

  const phSelect = h("select", {
    id: "ph-select",
    style: selectStyle(),
  }, h("option", { value: "" }, "대타 선택"));

  (manager.bench_for_ph || []).forEach((p) => {
    phSelect.appendChild(h("option", { value: p.name }, p.name));
  });

  const prSelect = h("select", {
    id: "pr-select",
    style: selectStyle(),
  }, h("option", { value: "" }, "대주자 선택"));

  (manager.bench_for_pr || []).forEach((p) => {
    prSelect.appendChild(h("option", { value: p.name }, p.name));
  });

  const prBaseSelect = h("select", {
    id: "pr-base-select",
    style: selectStyle(),
  });

  (manager.pr_base_choices || [1]).forEach((n) => {
    prBaseSelect.appendChild(h("option", { value: n }, `${n}루`));
  });

  const pitcherSelect = h("select", {
    id: "pitcher-select",
    style: selectStyle(),
  }, h("option", { value: "" }, "강제 투수 교체"));

  (manager.eligible_manual_pitchers || []).forEach((role) => {
    pitcherSelect.appendChild(h("option", { value: role }, role));
  });

  const managerCard = card(
    "감독 개입",
    h(
      "div",
      null,
      h(
        "div",
        {
          style: {
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "10px",
          },
        },
        h(
          "div",
          null,
          actionButton("다음 타석 강제 번트", () => emitAction("force_bunt"), !manager.can_force_bunt),
          h("div", { style: { height: "8px" } }),
          phSelect,
          h("div", { style: { height: "8px" } }),
          actionButton("대타 적용", () => emitAction("apply_ph", { name: phSelect.value }), !manager.bench_for_ph?.length)
        ),
        h(
          "div",
          null,
          prSelect,
          h("div", { style: { height: "8px" } }),
          prBaseSelect,
          h("div", { style: { height: "8px" } }),
          actionButton(
            "대주자 적용",
            () => emitAction("apply_pr", { name: prSelect.value, base_number: Number(prBaseSelect.value || 1) }),
            !manager.bench_for_pr?.length
          )
        )
      ),
      h("div", { style: { height: "10px" } }),
      pitcherSelect,
      h("div", { style: { height: "8px" } }),
      actionButton(
        "강제 투수 교체 적용",
        () => emitAction("apply_manual_pitcher", { role: pitcherSelect.value }),
        !manager.eligible_manual_pitchers?.length
      )
    )
  );

  grid.appendChild(stateCard);
  grid.appendChild(managerCard);
  wrap.appendChild(grid);

  const feedList = h("div", null);
  (game.feed_display || []).forEach((line) => {
    feedList.appendChild(
      h(
        "div",
        {
          style: {
            border: "1px solid #cbd5e1",
            borderRadius: "12px",
            padding: "10px 12px",
            background: "#fff",
            marginBottom: "8px",
            fontWeight: "700",
            color: "#334155",
          },
        },
        line
      )
    );
  });

  wrap.appendChild(card("최근 플레이 로그", feedList));

  root.appendChild(wrap);
  Streamlit.setFrameHeight(document.body.scrollHeight);
}

function infoRow(label, value) {
  return h(
    "div",
    {
      style: {
        display: "flex",
        justifyContent: "space-between",
        gap: "12px",
        padding: "9px 0",
        borderBottom: "1px solid #e2e8f0",
      },
    },
    h("div", { style: { color: "#64748b", fontWeight: "700" } }, label),
    h("div", { style: { color: "#0f172a", fontWeight: "900", textAlign: "right" } }, value)
  );
}

function selectStyle() {
  return {
    width: "100%",
    minHeight: "40px",
    borderRadius: "10px",
    border: "1px solid #cbd5e1",
    padding: "8px 10px",
    fontWeight: "700",
    background: "#fff",
  };
}

function onRender(event) {
  renderDashboard(event.detail.args);
}

window.addEventListener("load", () => {
  Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
  Streamlit.setComponentReady();
  Streamlit.setFrameHeight(400);
});