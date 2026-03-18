import React, { useEffect, useState } from "react";
import { Streamlit } from "streamlit-component-lib";
import { motion } from "framer-motion";
import fieldImage from "../../image/경기장 이미지.PNG";
import mainBg from "../../image/메인화면.png";
import logoHanwha from "../../image/한화.png";
import logoKIA from "../../image/KIA.png";
import logoKT from "../../image/KT.png";
import logoSSG from "../../image/SSG.png";
import logoNC from "../../image/NC.png";
import logoSamsung from "../../image/삼성.png";
import logoDoosan from "../../image/두산.png";
import logoLotte from "../../image/롯데.png";
import logoLG from "../../image/LG.png";
import logoKiwoom from "../../image/키움.png";

function emitAction(type, payload = {}) {
  Streamlit.setComponentValue({
    type,
    payload,
    nonce: Date.now(),
  });
}

function useAutoHeight(deps) {
  useEffect(() => {
    const t = window.setTimeout(() => {
      Streamlit.setFrameHeight(document.documentElement.scrollHeight);
    }, 100);

    // #region agent log
    fetch('http://127.0.0.1:7345/ingest/951d57bc-e6c4-4ece-8da0-0254437e8c89', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Debug-Session-Id': '0290f3',
      },
      body: JSON.stringify({
        sessionId: '0290f3',
        runId: 'pre-fix',
        hypothesisId: 'H2',
        location: 'HanwhaDashboard.jsx:useAutoHeight',
        message: 'setFrameHeight_called',
        data: {},
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion agent log
    return () => window.clearTimeout(t);
  }, deps);
}

function fmtText(v, fallback = "-") {
  if (v === null || v === undefined || v === "") return fallback;
  return String(v);
}

function Chip({ children }) {
  return <span className="ss-chip">{children}</span>;
}

function Card({ title, children, className = "" }) {
  return (
    <div className={`ss-card ${className}`}>
      <div className="ss-card-title">{title}</div>
      {children}
    </div>
  );
}

const TEAM_LOGOS = {
  한화: logoHanwha,
  KIA: logoKIA,
  KT: logoKT,
  SSG: logoSSG,
  NC: logoNC,
  삼성: logoSamsung,
  두산: logoDoosan,
  롯데: logoLotte,
  LG: logoLG,
  키움: logoKiwoom,
};

function TeamLogo({ team, size = 52 }) {
  const src = TEAM_LOGOS[team];
  if (!src) return <div className="ss-team-logo-fallback">{team}</div>;
  return <img src={src} alt={team} className="ss-team-logo" style={{ width: size, height: size }} />;
}

function InfoRow({ label, value }) {
  return (
    <div className="ss-info-row">
      <div className="ss-info-label">{label}</div>
      <div className="ss-info-value">{value}</div>
    </div>
  );
}

function TeamLine({ side, name, score, active }) {
  return (
    <div className={`ss-team-panel ${active ? "active" : ""}`}>
      <div className="ss-team-side">{side}</div>
      <div className="ss-team-name">{name}</div>
      <div className="ss-team-score">{score}</div>
    </div>
  );
}

function BaseDiamond({ active, label }) {
  return (
    <div className="ss-base-wrap">
      <div className={`ss-base ${active ? "active" : ""}`} />
      <div className="ss-base-label">{label}</div>
    </div>
  );
}

function LogFeed({ lines }) {
  if (!lines?.length) {
    return <div className="ss-empty">로그가 아직 없습니다.</div>;
  }

  return (
    <div className="ss-log-list">
      {lines.map((line, idx) => (
        <div key={`${idx}-${line}`} className="ss-log-item">
          {line}
        </div>
      ))}
    </div>
  );
}

function NoLiveGame({ selectedGame }) {
  return (
    <div className="ss-shell">
      <Card title="실시간 경기">
        <div className="ss-empty-block">
          <div className="ss-empty-title">아직 시작한 한화 경기가 없습니다.</div>
          <div className="ss-empty-sub">
            {selectedGame?.away && selectedGame?.home
              ? `${selectedGame.away} vs ${selectedGame.home}`
              : "오늘 한화 경기 정보 대기 중"}
          </div>
          <button className="ss-primary-btn" onClick={() => emitAction("start_or_resume")}>
            경기 시작 / 이어서 진행
          </button>
        </div>
      </Card>
    </div>
  );
}

function HomeHub({ summary, screens, onNavigate }) {
  const latest = summary?.latest_result_text || "-";
  const menus = [
    { id: "schedule", title: "오늘 일정", sub: "오늘 경기와 한화 진행", tone: "blue" },
    { id: "live", title: "실시간 경기", sub: "야구장 화면으로 시뮬", tone: "red" },
    { id: "lineup", title: "한화 라인업", sub: "선발/벤치 구성", tone: "gray" },
    { id: "trade", title: "트레이드", sub: "전력 강화", tone: "gold" },
    { id: "standings", title: "순위", sub: "리그 테이블", tone: "navy" },
    { id: "leaders", title: "리더보드", sub: "타자/투수 TOP", tone: "green" },
  ];

  return (
    <div className="ss-home">
        <div className="ss-home-bg">
          <img src={mainBg} alt="메인화면" className="ss-home-bg-img" loading="lazy" />
        <div className="ss-home-bg-overlay" />
      </div>

      <motion.div
        className="ss-home-top"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.28 }}
      >
        <div className="ss-home-title">효진부터 시작되는 한화의 KS 우승!</div>
        <div className="ss-home-sub">야구부스토리 감성 · 한화 수동 운영 + 자동 시뮬 + 리더보드</div>
        <div className="ss-home-badges">
          <span className="ss-home-badge">현재 날짜 · {fmtText(summary?.current_date)}</span>
          <span className="ss-home-badge">한화 순위 · {fmtText(summary?.hanwha_rank_text)}</span>
          <span className="ss-home-badge">완료 경기 · {fmtText(summary?.completed_game_count, "0")}</span>
          <span className="ss-home-badge ss-home-badge-strong">최근 결과 · {latest}</span>
        </div>
      </motion.div>

      <div className="ss-home-grid">
        {menus.map((m, idx) => (
          <motion.button
            key={m.id}
            className={`ss-home-card tone-${m.tone}`}
            onClick={() => onNavigate(m.id)}
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 * idx, duration: 0.25 }}
            whileHover={{ y: -3, scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            type="button"
          >
            <div className="ss-home-card-title">{m.title}</div>
            <div className="ss-home-card-sub">{m.sub}</div>
          </motion.button>
        ))}
      </div>

      <div className="ss-home-footer">
        <div className="ss-home-footer-note">메뉴를 클릭하면 해당 화면으로 전환됩니다.</div>
      </div>
    </div>
  );
}

function ScreenHeader({ title, onBack }) {
  return (
    <div className="ss-screen-header">
      <button className="ss-back-btn" onClick={onBack} type="button">← 메인</button>
      <div className="ss-screen-title">{title}</div>
    </div>
  );
}

function SimpleTable({ rows }) {
  if (!rows?.length) return <div className="ss-empty">표시할 데이터가 없습니다.</div>;
  const columns = Object.keys(rows[0] || {});
  return (
    <div className="ss-table-wrap">
      <div className="ss-table">
        <div className="ss-table-head">
          {columns.map((c) => <div key={`h-${c}`} className="ss-table-cell head">{c}</div>)}
        </div>
        {rows.map((r, i) => (
          <div key={`r-${i}`} className="ss-table-row">
            {columns.map((c) => <div key={`c-${i}-${c}`} className="ss-table-cell">{fmtText(r[c], "")}</div>)}
          </div>
        ))}
      </div>
    </div>
  );
}

function TradeScreen({ trade, onBack }) {
  const opponents = trade?.opponents || [];
  const markets = trade?.markets || {};
  const offerPool = trade?.offer_pool || [];
  const last = trade?.last_result || null;
  const month = trade?.month;
  const monthlyLimit = Number(trade?.monthly_limit || 1);
  const monthlyUsed = Number(trade?.monthly_used || 0);
  const monthlyRemaining = Math.max(0, monthlyLimit - monthlyUsed);

  const [opp, setOpp] = useState(opponents[0] || "");
  const [target, setTarget] = useState("");
  const [offered, setOffered] = useState([]);

  useEffect(() => {
    const list = markets?.[opp] || [];
    setTarget(list[0]?.name || "");
    setOffered([]);
  }, [opp]);

  const marketList = markets?.[opp] || [];

  return (
    <div className="ss-shell">
      <ScreenHeader title="트레이드" onBack={onBack} />

      {last?.message ? (
        <div className={`ss-trade-result ${last.ok ? "ok" : "bad"}`}>
          {last.ok ? "성공" : "실패"} · {last.message}
        </div>
      ) : null}

      <div className="ss-note" style={{ marginBottom: 14 }}>
        트레이드 월간 제한 · {fmtText(month, "-")} / 사용 {monthlyUsed}회 / 잔여 {monthlyRemaining}회
      </div>

      <div className="ss-two-col">
        <Card title="트레이드 제안">
          <div className="ss-form-block">
            <div className="ss-form-label">상대 팀</div>
            <select className="ss-select" value={opp} onChange={(e) => setOpp(e.target.value)}>
              {opponents.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div className="ss-form-block">
            <div className="ss-form-label">영입 대상</div>
            <select className="ss-select" value={target} onChange={(e) => setTarget(e.target.value)}>
              {(marketList || []).map((p) => (
                <option key={`${p.name}-${p.pos}`} value={p.name}>
                  {p.pos} / {p.name} (OPS {Number(p.ops || 0).toFixed(3)}, wRAA {Number(p.wraa || 0).toFixed(1)})
                </option>
              ))}
            </select>
          </div>

          <div className="ss-form-block">
            <div className="ss-form-label">제안 선수(한화 벤치)</div>
            <div className="ss-offer-grid">
              {offerPool.map((p) => {
                const checked = offered.includes(p.name);
                return (
                  <label key={p.name} className={`ss-offer-chip ${checked ? "on" : ""}`}>
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(e) => {
                        const on = e.target.checked;
                        setOffered((prev) => on ? [...prev, p.name] : prev.filter((x) => x !== p.name));
                      }}
                    />
                    <span>{p.pos} / {p.name}</span>
                  </label>
                );
              })}
            </div>
          </div>

          <button
            className="ss-primary-btn"
            onClick={() => emitAction("execute_trade", { opponent_team: opp, target_name: target, offered_names: offered })}
            disabled={!opp || !target || offered.length === 0 || monthlyRemaining <= 0}
            type="button"
          >
            {monthlyRemaining <= 0 ? "이번 달 트레이드 소진" : "트레이드 제안"}
          </button>
        </Card>

        <Card title="상대 팀 마켓 미리보기">
          <div className="ss-trade-market">
            {(marketList || []).slice(0, 40).map((p) => (
              <div key={`m-${p.name}-${p.pos}`} className="ss-trade-row">
                <div className="ss-trade-name">{p.pos} / {p.name}</div>
                <div className="ss-trade-meta">OPS {Number(p.ops || 0).toFixed(3)} · wRAA {Number(p.wraa || 0).toFixed(1)}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

export default function HanwhaDashboard(props) {
  const appPayload = props.args?.appPayload || {};
  const live = appPayload.live_game || {};
  const game = live.game_state || null;
  const manager = live.manager_actions || {};
  const summary = appPayload.season_summary || {};
  const screens = appPayload.screens || {};
  const lastError = screens?.last_error;

  const [screen, setScreen] = useState("home");
  const [loadingAction, setLoadingAction] = useState(null);

  const [phName, setPhName] = useState("");
  const [prName, setPrName] = useState("");
  const [prBase, setPrBase] = useState(1);
  const [manualRole, setManualRole] = useState("");

  // 라인업 드래그 상태 (Hook은 컴포넌트 최상단에만 선언)
  const [draggedStarter, setDraggedStarter] = useState(null);
  const [draggedPitcher, setDraggedPitcher] = useState(null);
  const [startersOrder, setStartersOrder] = useState([]);
  const [pitchersOrder, setPitchersOrder] = useState([]);

  const lineupStartersSource = screens?.hanwha_lineup?.starters || [];
  const lineupPitchersSource = screens?.hanwha_lineup?.starting_pitchers || [];

  useEffect(() => {
    if (manager.pr_base_choices?.length) {
      setPrBase(manager.pr_base_choices[0]);
    } else {
      setPrBase(1);
    }
  }, [manager.pr_base_choices]);

  // 서버 payload 변경 시 드래그용 로컬 상태 동기화
  useEffect(() => {
    setStartersOrder(lineupStartersSource);
  }, [lineupStartersSource.length, lineupStartersSource[0]?.name, lineupStartersSource[0]?.order]);

  useEffect(() => {
    setPitchersOrder(lineupPitchersSource);
  }, [lineupPitchersSource.length, lineupPitchersSource[0]?.name, lineupPitchersSource[0]?.role]);

  const bases = game?.bases || [];
  const base1 = !!bases[0];
  const base2 = !!bases[1];
  const base3 = !!bases[2];

  const lineAway = game?.line_score?.away_display || Array(9).fill("");
  const lineHome = game?.line_score?.home_display || Array(9).fill("");

  const currentBatter = game?.current_batter || {};
  const currentPitcher = game?.current_pitcher || {};

  const activeSide = game?.half === "top" ? "away" : "home";
  const hasLiveGame = !!live.has_live_game && !!game;

  const awayState = game?.away_state;
  const homeState = game?.home_state;
  const totals = game?.totals || {};
  const awayTotals = totals.away || {};
  const homeTotals = totals.home || {};

  const maxInnings = Math.max(
    11,
    (game?.line_score?.away?.length || 0),
    (game?.line_score?.home?.length || 0),
  );

  useAutoHeight([
    // 화면 종류가 바뀔 때만 전체 높이를 다시 계산하도록 제한
    screen,
  ]);

  // 액션 후 payload가 갱신되면 진행중 상태 자동 해제
  useEffect(() => {
    setLoadingAction(null);
  }, [game?.inning, game?.outs, game?.score?.away, game?.score?.home, game?.feed?.length, screen]);

  if (screen === "home") {
    return (
      <HomeHub
        summary={summary}
        screens={screens}
        onNavigate={(id) => setScreen(id)}
      />
    );
  }

  if (screen === "schedule") {
    const rows = screens?.today_schedule?.rows || [];
    const hgRows = screens?.hanwha_games?.rows || [];
    const hgDetail = screens?.hanwha_games?.detail || {};
    const selectedIdx = Number(screens?.hanwha_games?.selected_idx || 0);

    return (
      <div className="ss-shell">
        <ScreenHeader title="오늘 일정" onBack={() => setScreen("home")} />
        {lastError ? <div className="ss-error-banner">오류 · {lastError}</div> : null}

        <Card title={`오늘 전체 일정 (${fmtText(screens?.today_schedule?.date)})`}>
          <SimpleTable rows={rows} />
        </Card>

        <Card title="오늘 한화 경기">
          {hgRows.length ? (
            <div className="ss-form-block">
              <div className="ss-form-label">진행할 한화 경기 선택</div>
              <select
                className="ss-select"
                value={selectedIdx}
                onChange={(e) => emitAction("set_hanwha_game_idx", { idx: Number(e.target.value) })}
              >
                {hgRows.map((r, i) => (
                  <option key={`hg-${i}`} value={i}>
                    {fmtText(r.Away)} vs {fmtText(r.Home)}
                  </option>
                ))}
              </select>
            </div>
          ) : null}

          <div className="ss-hanwha-game-actions">
            <button className="ss-primary-btn" onClick={() => emitAction("start_or_resume")}>한화 경기 시작/이어서 진행</button>
            <button className="ss-secondary-btn" onClick={() => emitAction("simulate_selected")}>한화 경기 끝까지 + 나머지 자동</button>
            <button className="ss-secondary-btn" onClick={() => emitAction("simulate_day")}>오늘 경기 전부 자동</button>
          </div>

          <SimpleTable rows={hgRows} />
        </Card>

        {hgDetail?.selected_game ? (
          <Card title={`한화 vs ${fmtText(hgDetail?.selected_game?.opponent)} 상세 정보`}>
            <div className="ss-two-col">
              <div>
                <div className="ss-card-title">한화 선발 라인업</div>
                <div className="ss-live-lineup-list" style={{ maxHeight: 260 }}>
                  {(hgDetail?.hanwha_lineup || []).map((p) => (
                    <div key={`sch-h-${p.order}-${p.name}`} className="ss-live-lineup-row" style={{ background: '#fff' }}>
                      <div className="ss-live-lineup-left" style={{ color: '#0f172a' }}>{p.order}. {p.name} ({p.pos})</div>
                      <div className="ss-live-lineup-right">OPS {Number(p.ops || 0).toFixed(3)}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <div className="ss-card-title">상대 선발 라인업</div>
                <div className="ss-live-lineup-list" style={{ maxHeight: 260 }}>
                  {(hgDetail?.opponent_lineup || []).map((p) => (
                    <div key={`sch-o-${p.order}-${p.name}`} className="ss-live-lineup-row" style={{ background: '#fff' }}>
                      <div className="ss-live-lineup-left" style={{ color: '#0f172a' }}>{p.order}. {p.name} ({p.pos})</div>
                      <div className="ss-live-lineup-right">OPS {Number(p.ops || 0).toFixed(3)}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="ss-two-col" style={{ marginTop: 14 }}>
              <div className="ss-note">
                한화 선발투수 · {fmtText(hgDetail?.hanwha_starter?.name)} ({fmtText(hgDetail?.hanwha_starter?.role)}) · ERA {Number(hgDetail?.hanwha_starter?.era || 0).toFixed(2)} · WHIP {Number(hgDetail?.hanwha_starter?.whip || 0).toFixed(2)} · 체력 {fmtText(hgDetail?.hanwha_starter?.stamina, "100")}%
              </div>
              <div className="ss-note">
                상대 선발투수 · {fmtText(hgDetail?.opponent_starter?.name)} ({fmtText(hgDetail?.opponent_starter?.role)}) · ERA {Number(hgDetail?.opponent_starter?.era || 0).toFixed(2)} · WHIP {Number(hgDetail?.opponent_starter?.whip || 0).toFixed(2)} · 체력 {fmtText(hgDetail?.opponent_starter?.stamina, "100")}%
              </div>
            </div>

            <button className="ss-secondary-btn" onClick={() => setScreen("lineup")}>
              한화 라인업(타순/선발투수) 바로 편집
            </button>
          </Card>
        ) : null}
      </div>
    );
  }

  if (screen === "standings") {
    return (
      <div className="ss-shell">
        <ScreenHeader title="순위" onBack={() => setScreen("home")} />
        <Card title="현재 리그 순위">
          <SimpleTable rows={screens?.standings || []} />
        </Card>
      </div>
    );
  }

  if (screen === "leaders") {
    const batter_highlights = screens?.leaders?.batter_highlights || {};
    const pitcher_highlights = screens?.leaders?.pitcher_highlights || {};
    const batters = screens?.leaders?.batters || [];
    const pitchers = screens?.leaders?.pitchers || [];
    
    const renderTopCard = (title, data, stat_key) => {
      if (!data || data.length === 0) return null;
      return (
        <div key={title} className="ss-leader-card">
          <div className="ss-leader-title">{title}</div>
          {data.map((p, idx) => (
            <div key={`${idx}-${p['이름'] || p.name}`} className="ss-leader-item">
              <div className="ss-leader-badge">{idx + 1}</div>
              <div className="ss-leader-name">{p['이름'] || p.name}</div>
              <div className="ss-leader-value">{p[stat_key] || "-"}</div>
            </div>
          ))}
        </div>
      );
    };

    return (
      <div className="ss-shell">
        <ScreenHeader title="리더보드" onBack={() => setScreen("home")} />
        
        <div className="ss-leader-section">
          <div className="ss-leader-header">⭐ 타자 주요 기록 (TOP 5)</div>
          <div className="ss-leader-cards-row">
            {renderTopCard("홈런", batter_highlights["홈런"], "홈런")}
            {renderTopCard("안타", batter_highlights["안타"], "안타")}
            {renderTopCard("타율", batter_highlights["타율"], "타율")}
            {renderTopCard("출루율", batter_highlights["출루율"], "출루율")}
            {renderTopCard("OPS", batter_highlights["OPS"], "OPS")}
          </div>
        </div>

        <Card title="타자 전체 순위 (OPS 순 TOP20)">
          <SimpleTable rows={batters} />
        </Card>

        <div className="ss-leader-section">
          <div className="ss-leader-header">⭐ 투수 주요 기록 (TOP 5)</div>
          <div className="ss-leader-cards-row">
            {renderTopCard("ERA", pitcher_highlights["ERA"], "방어율")}
            {renderTopCard("WHIP", pitcher_highlights["WHIP"], "WHIP")}
            {renderTopCard("이닝", pitcher_highlights["이닝"], "이닝")}
            {renderTopCard("삼진", pitcher_highlights["삼진"], "탈삼진")}
            {renderTopCard("볼넷", pitcher_highlights["볼넷"], "볼넷")}
          </div>
        </div>

        <Card title="투수 전체 순위 (ERA 순 TOP20)">
          <SimpleTable rows={pitchers} />
        </Card>
      </div>
    );
  }

  if (screen === "lineup") {
    const bench = screens?.hanwha_lineup?.bench || [];
    const bullpen_pitchers = screens?.hanwha_lineup?.bullpen_pitchers || [];

    const handleStarterDragStart = (e, idx) => {
      setDraggedStarter(idx);
      e.dataTransfer.effectAllowed = "move";
    };

    const handleStarterDragOver = (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
    };

    const handleStarterDrop = (e, dropIdx) => {
      e.preventDefault();
      if (draggedStarter === null || draggedStarter === dropIdx) {
        setDraggedStarter(null);
        return;
      }

      const newOrder = [...startersOrder];
      const [removed] = newOrder.splice(draggedStarter, 1);
      newOrder.splice(dropIdx, 0, removed);

      const updatedOrder = newOrder.map((p, idx) => ({ ...p, order: idx + 1 }));
      setStartersOrder(updatedOrder);
      emitAction("update_batting_order", { new_order: updatedOrder.map((p) => p.name) });
      setDraggedStarter(null);
    };

    const handlePitcherDragStart = (e, idx) => {
      setDraggedPitcher(idx);
      e.dataTransfer.effectAllowed = "move";
    };

    const handlePitcherDragOver = (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
    };

    const handlePitcherDrop = (e, dropIdx) => {
      e.preventDefault();
      if (draggedPitcher === null || draggedPitcher === dropIdx) {
        setDraggedPitcher(null);
        return;
      }

      const newOrder = [...pitchersOrder];
      const [removed] = newOrder.splice(draggedPitcher, 1);
      newOrder.splice(dropIdx, 0, removed);

      setPitchersOrder(newOrder);
      emitAction("update_pitcher_rotation", { new_order: newOrder.map((p) => p.role) });
      setDraggedPitcher(null);
    };

    return (
      <div className="ss-shell">
        <ScreenHeader title="한화 라인업" onBack={() => setScreen("home")} />
        
        <div style={{ background: '#fff3e0', border: '2px solid var(--ss-hanwha)', borderRadius: '10px', padding: '12px', marginBottom: '16px', fontSize: '13px', color: '#d97706', fontWeight: 700 }}>
          💡 팁: 카드를 드래그해서 타순/로테이션을 변경할 수 있습니다. (다음 경기부터 적용됨)
        </div>
        
        <div className="ss-lineup-section">
          <div className="ss-lineup-header">🏟️ 타자 라인업</div>
          
          <div className="ss-lineup-cards">
            <Card title="선발 타자 (스타팅 9) - 드래그해서 타순 변경">
              <div className="ss-player-grid">
                {startersOrder.map((p, idx) => (
                  <div
                    key={`st-${idx}-${p.name}`}
                    className="ss-player-card"
                    draggable
                    onDragStart={(e) => handleStarterDragStart(e, idx)}
                    onDragOver={handleStarterDragOver}
                    onDrop={(e) => handleStarterDrop(e, idx)}
                    style={{
                      opacity: draggedStarter === idx ? 0.5 : 1,
                      cursor: 'move',
                      transition: 'opacity 0.2s'
                    }}
                  >
                    <div className="ss-player-num">{idx + 1}</div>
                    <div className="ss-player-name">{p.name}</div>
                    <div className="ss-player-pos">{p.pos}</div>
                    <div className="ss-player-stat">OPS {Number(p.ops || 0).toFixed(3)}</div>
                    <div className="ss-player-stat">타율 {p.avg != null ? Number(p.avg).toFixed(3) : "-"}</div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          <div className="ss-lineup-cards">
            <Card title="벤치 타자">
              <div className="ss-bench-list">
                {bench.map((p, idx) => (
                  <div key={`bn-${idx}-${p.name}`} className="ss-bench-item">
                    <span className="ss-bench-name">{p.pos} / {p.name}</span>
                    <span className="ss-bench-stat">OPS {Number(p.ops || 0).toFixed(3)}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>

        <div className="ss-lineup-section">
          <div className="ss-lineup-header">⚾ 투수 라인업</div>
          
          <div className="ss-lineup-cards">
            <Card title="선발 투수 로테이션 - 드래그해서 순서 변경">
              {pitchersOrder.length > 0 ? (
                <div className="ss-pitcher-grid">
                  {pitchersOrder.map((p, idx) => (
                    <div
                      key={`sp-${idx}-${p.name}`}
                      className="ss-pitcher-card"
                      draggable
                      onDragStart={(e) => handlePitcherDragStart(e, idx)}
                      onDragOver={handlePitcherDragOver}
                      onDrop={(e) => handlePitcherDrop(e, idx)}
                      style={{
                        opacity: draggedPitcher === idx ? 0.5 : 1,
                        cursor: 'move',
                        transition: 'opacity 0.2s'
                      }}
                    >
                      <div className="ss-pitcher-role">{p.role}</div>
                      <div className="ss-pitcher-name">{p.name}</div>
                      {p.next_game_starter ? <div className="ss-live-subnote" style={{ marginBottom: 6, padding: '4px 8px' }}>다음 경기 선발</div> : null}
                      <div className="ss-pitcher-stat">ERA {Number(p.era || 0).toFixed(3)}</div>
                      <div className="ss-pitcher-stat-sm">WHIP {Number(p.whip || 0).toFixed(3)} · 체력 {Number(p.stamina ?? 100)}%</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="ss-empty">선발 투수 정보 없음</div>
              )}
            </Card>
          </div>

          <div className="ss-lineup-cards">
            <Card title="불펜 투수">
              {bullpen_pitchers.length > 0 ? (
                <div className="ss-bullpen-list">
                  {bullpen_pitchers.map((p, idx) => (
                    <div key={`bp-${idx}-${p.name}`} className="ss-bullpen-item">
                      <span className="ss-bullpen-role">{p.role}</span>
                      <span className="ss-bullpen-name">{p.name}</span>
                      <span className="ss-bullpen-stat">ERA {Number(p.era || 0).toFixed(3)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="ss-empty">불펜 투수 정보 없음</div>
              )}
            </Card>
          </div>
        </div>
      </div>
    );
  }

  if (screen === "trade") {
    return <TradeScreen trade={screens?.trade} onBack={() => setScreen("home")} />;
  }

  if (screen === "live" && !hasLiveGame) {
    return (
      <div className="ss-shell">
        <ScreenHeader title="실시간 경기" onBack={() => setScreen("home")} />
        <NoLiveGame selectedGame={live.selected_game} />
      </div>
    );
  }

  if (screen !== "live") {
    // safety fallback
    setScreen("home");
    return null;
  }

  return (
    <div className="ss-shell">
      <ScreenHeader title="실시간 경기" onBack={() => setScreen("home")} />
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '16px' }}>
        <button
          className="ss-primary-btn"
          onClick={() => {
            setLoadingAction("live_pa");
            emitAction("live_pa");
          }}
          disabled={loadingAction === "live_pa"}
          style={{ marginBottom: 0, opacity: loadingAction === "live_pa" ? 0.6 : 1 }}
        >
          {loadingAction === "live_pa" ? "⏳ 진행중..." : "1타석 진행"}
        </button>
        <button
          className="ss-primary-btn"
          onClick={() => {
            setLoadingAction("live_half");
            emitAction("live_half");
          }}
          disabled={loadingAction === "live_half"}
          style={{ marginBottom: 0, opacity: loadingAction === "live_half" ? 0.6 : 1 }}
        >
          {loadingAction === "live_half" ? "⏳ 진행중..." : "반이닝 진행"}
        </button>
        <button
          className="ss-secondary-btn"
          onClick={() => {
            setLoadingAction("simulate_selected");
            emitAction("simulate_selected");
          }}
          disabled={loadingAction === "simulate_selected"}
          style={{ marginBottom: 0, opacity: loadingAction === "simulate_selected" ? 0.6 : 1 }}
        >
          {loadingAction === "simulate_selected" ? "⏳ 진행중..." : "경기 끝까지 진행"}
        </button>
      </div>

      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}>
        <div className="ss-scoreboard">
          <div className="ss-score-top">
            <div className="ss-team-side-wrap">
              <TeamLogo team={fmtText(game.away_team)} />
              <TeamLine side="AWAY" name={fmtText(game.away_team)} score={fmtText(game.score?.away, "0")} active={activeSide === "away"} />
            </div>
            <div className="ss-center-score-wrap">
              <div className="ss-center-score">{fmtText(game.score?.away, "0")} : {fmtText(game.score?.home, "0")}</div>
              <div className="ss-center-sub">{fmtText(summary.current_date)} · {fmtText(game.inning, "1")}회 {fmtText(game.half_kor)}</div>
            </div>
            <div className="ss-team-side-wrap ss-team-side-wrap-right">
              <TeamLine side="HOME" name={fmtText(game.home_team)} score={fmtText(game.score?.home, "0")} active={activeSide === "home"} />
              <TeamLogo team={fmtText(game.home_team)} />
            </div>
          </div>

          <div className="ss-chip-row">
            <Chip>{fmtText(game.inning, "1")}회 {fmtText(game.half_kor)}</Chip>
            <Chip>{fmtText(game.outs, "0")}아웃</Chip>
            <Chip>{fmtText(game.bases_text)}</Chip>
            <Chip>공격 {fmtText(game.offense_team)}</Chip>
            <Chip>수비 {fmtText(game.defense_team)}</Chip>
            <Chip>완료 경기 {fmtText(summary.completed_game_count, "0")}</Chip>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '16px' }}>
            <div style={{ background: 'linear-gradient(135deg, var(--ss-hanwha-light), white)', border: '2px solid var(--ss-hanwha)', borderRadius: '12px', padding: '12px', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--ss-sub)', fontWeight: 700, marginBottom: '4px' }}>현재 타자 🔥</div>
              <div style={{ fontSize: '14px', color: 'var(--ss-text)', fontWeight: 950 }}>{fmtText(currentBatter?.name, "-")}</div>
              <div style={{ fontSize: '10px', color: 'var(--ss-sub)', fontWeight: 700, marginTop: '4px' }}>{fmtText(currentBatter?.pos, "")} · {fmtText(currentBatter?.order, "")}번 타자</div>
            </div>
            <div style={{ background: 'linear-gradient(135deg, #E8D5F2, white)', border: '2px solid #7C3AED', borderRadius: '12px', padding: '12px', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: '#6d28d9', fontWeight: 700, marginBottom: '4px' }}>현재 투수 🔥</div>
              <div style={{ fontSize: '14px', color: 'var(--ss-text)', fontWeight: 950 }}>{fmtText(currentPitcher?.name, "-")}</div>
              <div style={{ fontSize: '10px', color: 'var(--ss-sub)', fontWeight: 700, marginTop: '4px' }}>{fmtText(currentPitcher?.role, "투수")}</div>
            </div>
          </div>

          <div className="ss-linescore">
            <div className="ss-linescore-header">
              <div className="ss-linescore-team">팀</div>
              {Array.from({ length: maxInnings }).map((_, i) => (
                <div key={`inn-h-${i}`} className="ss-linescore-cell">{i + 1}</div>
              ))}
              <div className="ss-linescore-total">R</div>
              <div className="ss-linescore-total">H</div>
              <div className="ss-linescore-total">E</div>
              <div className="ss-linescore-total">B</div>
            </div>

            <div className={`ss-linescore-row ${activeSide === "away" ? "active" : ""}`}>
              <div className="ss-linescore-team">{fmtText(game.away_team)}</div>
              {Array.from({ length: maxInnings }).map((_, i) => (
                <div key={`away-${i}`} className="ss-linescore-cell">
                  {fmtText(lineAway[i] ?? "", "")}
                </div>
              ))}
              <div className="ss-linescore-total">{fmtText(awayTotals.R, "0")}</div>
              <div className="ss-linescore-total">{fmtText(awayTotals.H, "0")}</div>
              <div className="ss-linescore-total">{fmtText(awayTotals.E, "0")}</div>
              <div className="ss-linescore-total">{fmtText(awayTotals.B, "0")}</div>
            </div>

            <div className={`ss-linescore-row ${activeSide === "home" ? "active" : ""}`}>
              <div className="ss-linescore-team">{fmtText(game.home_team)}</div>
              {Array.from({ length: maxInnings }).map((_, i) => (
                <div key={`home-${i}`} className="ss-linescore-cell">
                  {fmtText(lineHome[i] ?? "", "")}
                </div>
              ))}
              <div className="ss-linescore-total">{fmtText(homeTotals.R, "0")}</div>
              <div className="ss-linescore-total">{fmtText(homeTotals.H, "0")}</div>
              <div className="ss-linescore-total">{fmtText(homeTotals.E, "0")}</div>
              <div className="ss-linescore-total">{fmtText(homeTotals.B, "0")}</div>
            </div>
          </div>

          <div className="ss-live-mid-grid">
            <div className="ss-live-field-stage">
              <div className="ss-field-photo-wrap">
                <img src={fieldImage} alt="야구장" className="ss-field-photo" loading="lazy" />
                <div className="ss-base-runner ss-base-runner-1b">
                  {bases?.[0]?.name ? `${bases[0].name}` : "1루"}
                </div>
                <div className="ss-base-runner ss-base-runner-2b">
                  {bases?.[1]?.name ? `${bases[1].name}` : "2루"}
                </div>
                <div className="ss-base-runner ss-base-runner-3b">
                  {bases?.[2]?.name ? `${bases[2].name}` : "3루"}
                </div>
              </div>
            </div>

            <div className="ss-live-side-panel">
              <div className="ss-live-lineup-card">
                <div className="ss-live-lineup-title">AWAY 라인업</div>
                <div className="ss-live-lineup-list">
                  {(awayState?.lineup || []).map((p) => {
                    const isCurrent = activeSide === "away" && String(p.name) === String(currentBatter?.name);
                    return (
                      <div key={`away-lineup-${p.order}-${p.name}`} className={`ss-live-lineup-row ${isCurrent ? "current" : ""}`}>
                        <div className="ss-live-lineup-left">{p.order}. {p.name} ({p.pos})</div>
                        <div className="ss-live-lineup-right">{p.today_avg != null ? Number(p.today_avg).toFixed(3) : "-"}</div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="ss-live-lineup-card away-tone">
                <div className="ss-live-lineup-title">HOME 라인업</div>
                <div className="ss-live-lineup-list">
                  {(homeState?.lineup || []).map((p) => {
                    const isCurrent = activeSide === "home" && String(p.name) === String(currentBatter?.name);
                    return (
                      <div key={`home-lineup-${p.order}-${p.name}`} className={`ss-live-lineup-row ${isCurrent ? "current" : ""}`}>
                        <div className="ss-live-lineup-left">{p.order}. {p.name} ({p.pos})</div>
                        <div className="ss-live-lineup-right">{p.today_avg != null ? Number(p.today_avg).toFixed(3) : "-"}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      <Card title="감독 개입">
        <div className="ss-form-block">
          <button className="ss-primary-btn" onClick={() => emitAction("force_bunt")} disabled={!manager.can_force_bunt}>
            다음 타석 강제 번트
          </button>
        </div>

        <div className="ss-form-block">
          <div className="ss-form-label">대타</div>
          <div className="ss-live-subnote">OUT {fmtText(currentBatter?.name, "-")} → IN {fmtText(phName, "선택 대기")}</div>
          <select className="ss-select" value={phName} onChange={(e) => setPhName(e.target.value)}>
            <option value="">대타 선택</option>
            {(manager.bench_for_ph || []).map((p) => (
              <option key={p.name} value={p.name}>{p.name}</option>
            ))}
          </select>
          <button className="ss-secondary-btn" onClick={() => emitAction("apply_ph", { name: phName })} disabled={!phName}>
            대타 적용
          </button>
        </div>

        <div className="ss-form-block">
          <div className="ss-form-label">대주자</div>
          <div className="ss-live-subnote">OUT {fmtText(bases?.[Number(prBase || 1) - 1]?.name, "주자 없음")} → IN {fmtText(prName, "선택 대기")}</div>
          <select className="ss-select" value={prName} onChange={(e) => setPrName(e.target.value)}>
            <option value="">대주자 선택</option>
            {(manager.bench_for_pr || []).map((p) => (
              <option key={p.name} value={p.name}>{p.name}</option>
            ))}
          </select>

          <select className="ss-select" value={prBase} onChange={(e) => setPrBase(Number(e.target.value))}>
            {(manager.pr_base_choices?.length ? manager.pr_base_choices : [1]).map((b) => (
              <option key={b} value={b}>{b}루</option>
            ))}
          </select>

          <button className="ss-secondary-btn" onClick={() => emitAction("apply_pr", { name: prName, base_number: prBase })} disabled={!prName}>
            대주자 적용
          </button>
        </div>

        <div className="ss-form-block">
          <div className="ss-form-label">강제 투수 교체</div>
          <div className="ss-live-subnote">OUT {fmtText(currentPitcher?.name, "-")} → IN {fmtText(manualRole, "선택 대기")}</div>
          <select className="ss-select" value={manualRole} onChange={(e) => setManualRole(e.target.value)}>
            <option value="">역할 선택</option>
            {(manager.eligible_manual_pitchers || []).map((role) => (
              <option key={role} value={role}>{role}</option>
            ))}
          </select>
          <button className="ss-secondary-btn" onClick={() => emitAction("apply_manual_pitcher", { role: manualRole })} disabled={!manualRole}>
            강제 투수 교체 적용
          </button>
        </div>

        <div className="ss-note">현재 액션은 Python 시뮬 엔진으로 돌아가고, 이 패널은 React UI 레이어만 담당합니다.</div>
      </Card>

      <div className="ss-bottom-grid">
        <Card title="현재 타석 매치업">
          <InfoRow label="타자" value={`${fmtText(currentBatter.name)}${currentBatter.pos ? ` / ${currentBatter.pos}` : ""}`} />
          <InfoRow label="타순" value={fmtText(currentBatter.order, "-")} />
          <InfoRow label="OPS" value={currentBatter.ops !== undefined ? Number(currentBatter.ops).toFixed(3) : "-"} />
          <InfoRow label="wRAA" value={currentBatter.wraa !== undefined ? Number(currentBatter.wraa).toFixed(1) : "-"} />
          <InfoRow label="투수" value={`${fmtText(currentPitcher.name)}${currentPitcher.role ? ` / ${currentPitcher.role}` : ""}`} />
        </Card>

        <Card title="최근 플레이 로그">
          <LogFeed lines={game.feed_display || []} />
        </Card>
      </div>
    </div>
  );
}
