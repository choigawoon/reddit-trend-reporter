import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  BarChart3,
  BriefcaseBusiness,
  CalendarClock,
  CheckCircle2,
  ExternalLink,
  Filter,
  Github,
  Quote,
  MessageCircle,
  Rocket,
  RefreshCw,
  Search,
  ShieldAlert,
  Sparkles,
  Star,
  Terminal,
  TrendingUp,
  TriangleAlert,
} from 'lucide-react';
import './styles.css';

const numberFmt = new Intl.NumberFormat('en-US');

function flattenPosts(data) {
  return (data?.subreddits || []).flatMap((sub) =>
    (sub.posts || []).map((post) => ({
      ...post,
      subredditName: sub.name,
    })),
  );
}

function flattenTrending(data) {
  return (data?.subreddits || []).flatMap((sub) =>
    (sub.trending?.posts || []).map((post) => ({
      ...post,
      subredditName: sub.name,
    })),
  );
}

const LEGACY_MANIFEST = {
  profiles: [
    { id: 'trend', label: 'Report', kind: 'trend', latest: 'data/latest.json', index: 'data/index.json', has_data: true },
  ],
};

function dirOf(path) {
  return String(path || '').replace(/[^/]*$/, '');
}

function App() {
  const [manifest, setManifest] = useState(null);
  const [activeProfileId, setActiveProfileId] = useState(null);
  const [data, setData] = useState(null);
  const [activeData, setActiveData] = useState(null);
  const [reportIndex, setReportIndex] = useState(null);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [flair, setFlair] = useState('all');
  const [sort, setSort] = useState('rank');
  const [page, setPage] = useState('report');

  // 1) load the profile manifest once (falls back to single legacy profile)
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/profiles.json`, { cache: 'no-store' })
      .then((res) => (res.ok ? res.json() : LEGACY_MANIFEST))
      .then((m) => (m && Array.isArray(m.profiles) && m.profiles.length ? m : LEGACY_MANIFEST))
      .catch(() => LEGACY_MANIFEST)
      .then((m) => {
        setManifest(m);
        setActiveProfileId((prev) => prev || m.profiles[0].id);
      });
  }, []);

  const activeProfile = useMemo(() => {
    if (!manifest) return null;
    return manifest.profiles.find((p) => p.id === activeProfileId) || manifest.profiles[0];
  }, [manifest, activeProfileId]);

  // 2) load the active profile's latest report + archive index
  useEffect(() => {
    if (!activeProfile) return;
    setError('');
    setData(null);
    setActiveData(null);
    setReportIndex(null);
    setPage('report');
    fetch(`${import.meta.env.BASE_URL}${activeProfile.latest}`, { cache: 'no-store' })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((payload) => {
        setData(payload);
        setActiveData(payload);
      })
      .catch((err) => {
        // a scaffold profile may have no data yet — not a hard error
        if (activeProfile.has_data) setError(String(err));
      });
    fetch(`${import.meta.env.BASE_URL}${activeProfile.index}`, { cache: 'no-store' })
      .then((res) => (res.ok ? res.json() : { reports: [] }))
      .then(setReportIndex)
      .catch(() => setReportIndex({ reports: [] }));
  }, [activeProfile]);

  const posts = useMemo(() => flattenPosts(activeData), [activeData]);
  const trendingPosts = useMemo(() => flattenTrending(activeData), [activeData]);
  const flairs = useMemo(() => {
    const values = new Set(posts.map((post) => post.flair || 'Unflaired'));
    return ['all', ...Array.from(values).sort()];
  }, [posts]);

  const filteredPosts = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const filtered = posts.filter((post) => {
      const matchesQuery = !needle || `${post.title} ${post.text || ''}`.toLowerCase().includes(needle);
      const postFlair = post.flair || 'Unflaired';
      const matchesFlair = flair === 'all' || postFlair === flair;
      return matchesQuery && matchesFlair;
    });
    return [...filtered].sort((a, b) => {
      if (sort === 'score') return b.score - a.score;
      if (sort === 'comments') return b.comments - a.comments;
      return a.rank - b.rank;
    });
  }, [posts, query, flair, sort]);

  const analysis = activeData?.analysis;
  const topScore = posts[0]?.score || 0;
  const commentTotal = posts.reduce((sum, post) => sum + (post.comments || 0), 0);
  const isTrend = (activeProfile?.kind || 'trend') === 'trend';

  if (!manifest || !activeProfile) {
    return <main className="status">Loading…</main>;
  }
  if (error) {
    return <main className="status">Failed to load report: {error}</main>;
  }

  const indexDir = dirOf(activeProfile.index);

  return (
    <main>
      {manifest.profiles.length > 1 && (
        <nav className="profileNav">
          {manifest.profiles.map((p) => (
            <button
              key={p.id}
              className={p.id === activeProfile.id ? 'active' : ''}
              onClick={() => setActiveProfileId(p.id)}
            >
              {p.label}
              {!p.has_data && <span className="profileDot" title="아직 데이터 없음">●</span>}
            </button>
          ))}
        </nav>
      )}

      <nav className="topNav">
        <button className={page === 'report' ? 'active' : ''} onClick={() => setPage('report')}>Live Report</button>
        <button className={page === 'reports' ? 'active' : ''} onClick={() => setPage('reports')}>Reports</button>
        {isTrend && <button className={page === 'decision' ? 'active' : ''} onClick={() => setPage('decision')}>Decision Inputs</button>}
        <button className={page === 'landing' ? 'active' : ''} onClick={() => setPage('landing')}>Why</button>
        <button className={page === 'manual' ? 'active' : ''} onClick={() => setPage('manual')}>How</button>
      </nav>

      {page === 'landing' && <Landing data={activeData} posts={posts} setPage={setPage} />}
      {page === 'reports' && <Reports index={reportIndex} indexDir={indexDir} setActiveData={setActiveData} setPage={setPage} latestData={data} />}
      {page === 'manual' && <Manual />}
      {page === 'decision' && isTrend && <DecisionInputs analysis={analysis} posts={posts} />}
      {page === 'report' && (
        isTrend ? (
          activeData ? (
            <Report
              data={activeData}
              posts={posts}
              trendingPosts={trendingPosts}
              analysis={analysis}
              filteredPosts={filteredPosts}
              flairs={flairs}
              query={query}
              setQuery={setQuery}
              flair={flair}
              setFlair={setFlair}
              sort={sort}
              setSort={setSort}
              topScore={topScore}
              commentTotal={commentTotal}
            />
          ) : (
            <section className="status">리포트를 불러오는 중…</section>
          )
        ) : (
          <ScaffoldProfile profile={activeProfile} data={activeData} posts={posts} trendingPosts={trendingPosts} />
        )
      )}
    </main>
  );
}

function Landing({ data, posts, setPage }) {
  const analysis = data?.analysis;
  const topPost = posts[0];
  return (
    <>
      <section className="salesHero">
        <div className="salesCopy">
          <p className="eyebrow">Scheduled Reddit Intelligence</p>
          <h1>커뮤니티에서 터지는 신호를 매일 리포트로 바꾸는 정적 웹 대시보드</h1>
          <p className="summary">
            Reddit 서브레딧의 top·rising 글과 상위 댓글을 매일 자동 수집하고, Claude가 트렌드·커뮤니티 반응·상업성 판단을 JSON으로 정리합니다.
            결과는 GitHub Pages에 올릴 수 있는 정적 웹페이지로 남아 팀이 링크 하나로 확인합니다.
          </p>
          <div className="heroActions">
            <button onClick={() => setPage('report')}>리포트 보기</button>
            <button className="secondary" onClick={() => setPage('reports')}>개별 리포트</button>
            <button className="secondary" onClick={() => setPage('decision')}>의사결정 재료</button>
            <button className="secondary" onClick={() => setPage('manual')}>How</button>
          </div>
        </div>
        <div className="heroPreview" aria-label="live report preview">
          <div className="previewHeader">
            <Sparkles size={18} />
            <span>{analysis?.headline || 'Latest trend snapshot'}</span>
          </div>
          <div className="previewChart">
            {posts.slice(0, 8).map((post) => (
              <div key={post.id} style={{ height: `${Math.max(18, Math.min(100, post.score / 14))}%` }} title={post.title} />
            ))}
          </div>
          {topPost && (
            <div className="previewPost">
              <strong>#{topPost.rank} {topPost.title}</strong>
              <span>{numberFmt.format(topPost.score)} score · {numberFmt.format(topPost.comments)} comments</span>
            </div>
          )}
        </div>
      </section>

      <section className="problemGrid">
        <Panel title="해결하는 문제">
          <ul className="checkList">
            <li><CheckCircle2 size={18} /> 매번 Reddit을 직접 훑어봐야 하는 반복 조사</li>
            <li><CheckCircle2 size={18} /> 어떤 글이 진짜 화제인지 점수와 댓글을 따로 봐야 하는 번거로움</li>
            <li><CheckCircle2 size={18} /> LLM 요약 결과가 일회성 채팅으로 사라지는 문제</li>
          </ul>
        </Panel>
        <Panel title="솔루션">
          <ul className="checkList">
            <li><CheckCircle2 size={18} /> 수집은 스크립트, 판단은 Claude, 배포는 정적 페이지로 분리</li>
            <li><CheckCircle2 size={18} /> 매일/매주 cron으로 자동 업데이트</li>
            <li><CheckCircle2 size={18} /> GitHub Pages에 배포해 공유 가능한 링크 제공</li>
          </ul>
        </Panel>
        <Panel title="대상 사용자">
          <ul className="checkList">
            <li><CheckCircle2 size={18} /> AI 제품/콘텐츠 리서처</li>
            <li><CheckCircle2 size={18} /> 커뮤니티 반응을 보는 마케터</li>
            <li><CheckCircle2 size={18} /> 모델/툴 트렌드를 추적하는 개발팀</li>
          </ul>
        </Panel>
      </section>

      <section className="flowBand">
        <h2>작동 방식</h2>
        <div className="flowSteps">
          <div><strong>1. Collect</strong><span>rdt-cli로 top·rising 글과 상위 댓글 수집</span></div>
          <div><strong>2. Analyze</strong><span>claude -p가 트렌드·커뮤니티 반응·상업성을 JSON으로 작성</span></div>
          <div><strong>3. Publish</strong><span>Vite 정적 페이지를 GitHub Pages로 배포</span></div>
        </div>
      </section>
    </>
  );
}

function DecisionInputs({ analysis, posts }) {
  return (
    <>
      <CommunityVoice analysis={analysis} posts={posts} embedded />
      <Commercial analysis={analysis} posts={posts} embedded />
    </>
  );
}

function CommunityVoice({ analysis, posts, embedded = false }) {
  const voice = analysis?.community_voice;
  const evidenceMap = useMemo(() => new Map(posts.map((post) => [post.id, post])), [posts]);
  const enrichedPosts = posts.filter((post) => post.discussion?.comments?.length);

  if (!voice) {
    return (
      <section className="hero manualHero">
        <div>
          <p className="eyebrow">Community Voice</p>
          <h1>댓글 기반 정성평가가 아직 없습니다</h1>
          <p className="summary">새 파이프라인으로 다시 실행하면 상위 포스트의 본문과 댓글을 수집해 정성평가를 생성합니다.</p>
        </div>
      </section>
    );
  }

  return (
    <>
      <section className="hero voiceHero">
        <div>
          <p className="eyebrow">Community Voice</p>
          <h1>{embedded ? '본문과 댓글을 읽어 정리한 실제 반응' : '본문과 댓글을 읽어 정리한 실제 반응'}</h1>
          <p className="summary">{voice.summary}</p>
        </div>
        <div className={`sentimentCard ${voice.sentiment || 'unclear'}`}>
          <span>Sentiment</span>
          <strong>{voice.sentiment}</strong>
          <p>Confidence {Math.round((voice.confidence || 0) * 100)}%</p>
        </div>
      </section>

      <section className="voiceGrid">
        <VoicePanel title="Praise" items={voice.praise || []} evidenceMap={evidenceMap} />
        <VoicePanel title="Complaints" items={voice.complaints || []} evidenceMap={evidenceMap} />
        <VoicePanel title="Adoption Blockers" items={voice.adoption_blockers || []} evidenceMap={evidenceMap} />
      </section>

      <section className="analysisGrid">
        <Panel title="Model Reputation Notes">
          {(voice.model_reputation_notes || []).map((item) => (
            <article className="topic" key={`${item.model}-${item.note}`}>
              <h3>{item.model}</h3>
              <p>{item.note}</p>
              <div className="ids">{[...(item.evidence_post_ids || []), ...(item.evidence_comment_ids || [])].join(', ')}</div>
            </article>
          ))}
        </Panel>
        <Panel title="Representative Quotes">
          <div className="quoteList">
            {(voice.representative_quotes || []).map((item) => (
              <blockquote key={`${item.comment_id || item.post_id}-${item.quote}`}>
                <Quote size={16} />
                <p>{item.quote}</p>
                <span>{item.kind} · {item.post_id}{item.comment_id ? ` / ${item.comment_id}` : ''}</span>
              </blockquote>
            ))}
          </div>
        </Panel>
        <Panel title="Collected Threads">
          <ul className="plainList">
            {enrichedPosts.map((post) => (
              <li key={post.id}>
                <strong>#{post.rank} {post.title}</strong>
                <span>{post.discussion.comments.length} comments collected</span>
              </li>
            ))}
          </ul>
        </Panel>
      </section>
    </>
  );
}

function VoicePanel({ title, items, evidenceMap }) {
  return (
    <section className="voicePanel">
      <h2>{title}</h2>
      {items.map((item) => (
        <article key={item.point}>
          <p>{item.point}</p>
          <Evidence ids={item.evidence_post_ids || []} evidenceMap={evidenceMap} />
          {(item.evidence_comment_ids || []).length > 0 && <div className="ids">comments: {item.evidence_comment_ids.join(', ')}</div>}
        </article>
      ))}
    </section>
  );
}

function Reports({ index, indexDir = 'data/', setActiveData, setPage, latestData }) {
  const reports = index?.reports || [];

  function openLatest() {
    setActiveData(latestData);
    setPage('report');
  }

  function openReport(item) {
    fetch(`${import.meta.env.BASE_URL}${indexDir}${item.path}`, { cache: 'no-store' })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((payload) => {
        setActiveData(payload);
        setPage('report');
      });
  }

  return (
    <>
      <section className="hero manualHero">
        <div>
          <p className="eyebrow">Report Archive</p>
          <h1>실행별 리포트를 개별 페이지처럼 열어 비교</h1>
          <p className="summary">스케줄이 돌 때마다 별도 JSON 리포트가 생성됩니다. 최신 리포트는 기본 화면에 요약되고, 과거 실행분은 여기서 개별로 열 수 있습니다.</p>
          <div className="heroActions">
            <button onClick={openLatest}>최신 리포트 열기</button>
          </div>
        </div>
      </section>

      <section className="reportArchive">
        {reports.map((item) => (
          <article className="reportItem" key={item.path}>
            <div>
              <span>{new Date(item.generated_at).toLocaleString()}</span>
              <h2>{item.subreddits.map((subreddit) => `r/${subreddit}`).join(', ')}</h2>
              <p>{item.sort}/{item.time} · {item.post_count} posts</p>
            </div>
            <button onClick={() => openReport(item)}>Open</button>
          </article>
        ))}
      </section>
    </>
  );
}

function Commercial({ analysis, posts, embedded = false }) {
  const commercial = analysis?.commercial;
  const evidenceMap = useMemo(() => new Map(posts.map((post) => [post.id, post])), [posts]);

  if (!commercial) {
    return (
      <section className="hero manualHero">
        <div>
          <p className="eyebrow">Commercial Decision</p>
          <h1>상업 활용 판단 데이터가 아직 없습니다</h1>
          <p className="summary">`npm run report` 또는 `npm run pipeline -- --allow-fallback`을 다시 실행하면 새 스키마로 상업성 평가가 생성됩니다.</p>
        </div>
      </section>
    );
  }

  return (
    <>
      <section className="hero commercialHero">
        <div>
          <p className="eyebrow">Commercial Decision</p>
          <h1>{embedded ? '상업적 판단에 필요한 실행 재료' : '원재료를 실행 가능한 사업 판단으로 정제'}</h1>
          <p className="summary">{commercial.summary}</p>
        </div>
        <div className={`verdictCard ${String(commercial.verdict || '').toLowerCase()}`}>
          <span>Verdict</span>
          <strong>{commercial.verdict}</strong>
          <p>Confidence {Math.round((commercial.confidence || 0) * 100)}%</p>
        </div>
      </section>

      <section className="commercialGrid">
        {(commercial.opportunities || []).map((item) => (
          <article className="opportunity" key={item.title}>
            <div className="opportunityTop">
              <BriefcaseBusiness size={20} />
              <div>
                <h2>{item.title}</h2>
                <span>{item.customer}</span>
              </div>
            </div>
            <p>{item.use_case}</p>
            <dl>
              <div>
                <dt>수익화/효율화</dt>
                <dd>{item.monetization}</dd>
              </div>
              <div>
                <dt>실행 난이도</dt>
                <dd>{item.effort}</dd>
              </div>
              <div>
                <dt>리스크</dt>
                <dd>{item.risk}</dd>
              </div>
            </dl>
            <Evidence ids={item.evidence_post_ids || []} evidenceMap={evidenceMap} />
          </article>
        ))}
      </section>

      <section className="decisionGrid">
        <DecisionPanel icon={<Rocket size={19} />} title="Do Now" items={commercial.do_now || []} />
        <DecisionPanel icon={<Search size={19} />} title="Watch" items={commercial.watch || []} />
        <DecisionPanel icon={<ShieldAlert size={19} />} title="Avoid / Review" items={commercial.avoid_or_review || []} warning />
      </section>

      <Panel title="Decision Notes">
        <ul className="compactList">{(commercial.decision_notes || []).map((item) => <li key={item}>{item}</li>)}</ul>
      </Panel>
    </>
  );
}

function Evidence({ ids, evidenceMap }) {
  if (!ids.length) return null;
  return (
    <div className="evidence">
      <strong>Evidence</strong>
      {ids.map((id) => {
        const post = evidenceMap.get(id);
        return (
          <a key={id} href={post?.reddit_url || '#'} target="_blank" rel="noreferrer">
            {post ? `#${post.rank} ${post.title}` : id}
            <ExternalLink size={13} />
          </a>
        );
      })}
    </div>
  );
}

function DecisionPanel({ icon, title, items, warning = false }) {
  return (
    <section className={`decisionPanel ${warning ? 'warning' : ''}`}>
      <h2>{icon}{title}</h2>
      <ul>
        {items.map((item) => (
          <li key={item}>{warning && <TriangleAlert size={16} />}{item}</li>
        ))}
      </ul>
    </section>
  );
}

function Manual() {
  return (
    <>
      <section className="hero manualHero">
        <div>
          <p className="eyebrow">How</p>
          <h1>각자 머신에 설치하고 GitHub Pages로 배포하는 방법</h1>
          <p className="summary">Reddit 로그인 쿠키와 Claude CLI가 있는 개인 머신에서 스케줄을 걸고, 생성된 JSON을 GitHub로 push하면 GitHub Pages가 자동으로 최신 정적 리포트를 배포합니다.</p>
        </div>
      </section>

      <section className="manualGrid">
        <Panel title="1. 설치">
          <CodeBlock>{`git clone <repo-url>
cd reddit-trend-reporter
npm run setup   # npm + uv + rdt-cli 자동 설치, claude 확인
rdt status --json

# 데이터 파이프라인만 어디서나 쓰려면 (rdt-cli 동봉)
uv tool install git+<repo-url>
reddit-report --version`}</CodeBlock>
        </Panel>
        <Panel title="2. 수집 대상 수정">
          <CodeBlock>{`# config/reddit-report.json
{
  "subreddits": ["StableDiffusion"],
  "sort": "top",
  "time": "day",
  "limit": 30,
  "trending": { "sort": "rising", "limit": 15 }
}`}</CodeBlock>
        </Panel>
        <Panel title="3. 한번 실행">
          <CodeBlock>{`npm run pipeline -- --allow-fallback
npm run preview`}</CodeBlock>
        </Panel>
        <Panel title="4. 매일 실행 cron">
          <CodeBlock>{`0 9 * * * cd /path/to/reddit-trend-reporter && npm run pipeline -- --allow-fallback >> logs/pipeline.log 2>&1`}</CodeBlock>
        </Panel>
        <Panel title="5. GitHub Pages 배포">
          <CodeBlock>{`git pull --ff-only
npm run pipeline -- --allow-fallback
git add public/data data/runs
git commit -m "Update Reddit trend report"
git push`}</CodeBlock>
        </Panel>
        <Panel title="6. 자기 repo로 배포">
          <CodeBlock>{`gh repo create <github-id>/reddit-trend-reporter --public --source=. --remote=origin --push
gh api --method POST repos/<github-id>/reddit-trend-reporter/pages -f build_type=workflow

# 배포 URL
https://<github-id>.github.io/reddit-trend-reporter/`}</CodeBlock>
        </Panel>
        <Panel title="운영 체크">
          <ul className="checkList">
            <li><Terminal size={18} /> `rdt status --json`에서 authenticated 확인</li>
            <li><Github size={18} /> GitHub Pages는 repo Settings에서 Pages source를 Actions로 설정</li>
            <li><RefreshCw size={18} /> Reddit 쿠키 만료 시 브라우저 재로그인 후 credential 갱신</li>
          </ul>
        </Panel>
      </section>
    </>
  );
}

function TrendingSection({ trendingPosts = [], posts = [], sortLabel }) {
  const topIds = useMemo(() => new Set(posts.map((post) => post.id)), [posts]);
  if (!trendingPosts.length) return null;
  return (
    <section className="trending" aria-label="trending posts">
      <div className="trendingHead">
        <TrendingUp size={18} />
        <h2>Trending · {sortLabel || 'rising'}</h2>
        <span>지금 빠르게 오르는 글 (top과 별개로 떠오르는 신호)</span>
      </div>
      <div className="trendingList">
        {trendingPosts.slice(0, 12).map((post) => (
          <a className="trendingItem" key={`trend-${post.id}`} href={post.reddit_url} target="_blank" rel="noreferrer">
            <span className="trendingRank"><TrendingUp size={13} />{post.rank}</span>
            <div className="trendingBody">
              <strong>{post.title}</strong>
              <span className="trendingMeta">
                r/{post.subredditName} · {numberFmt.format(post.score)} score · {numberFmt.format(post.comments)} comments
                {!topIds.has(post.id) && <em className="trendingNew">NEW</em>}
              </span>
            </div>
            <ExternalLink size={14} />
          </a>
        ))}
      </div>
    </section>
  );
}

function ScaffoldProfile({ profile, data, posts = [], trendingPosts = [] }) {
  const analysis = data?.analysis;
  const commentTotal = posts.reduce((sum, post) => sum + (post.comments || 0), 0);
  return (
    <>
      <section className="hero">
        <div>
          <p className="eyebrow">{profile.label}</p>
          <h1>{analysis?.headline || `${profile.label} (스캐폴드)`}</h1>
          <p className="summary">
            {analysis?.summary || '이 프로파일은 설계틀(skeleton) 상태입니다. 아래 명령으로 수집·분석을 실행하면 채워집니다.'}
          </p>
        </div>
        <div className="metaPanel" aria-label="profile metadata">
          <div><Sparkles size={18} /><span>profile: {profile.id} · {profile.kind}</span></div>
          {data?.generated_at && (
            <div><CalendarClock size={18} /><span>{new Date(data.generated_at).toLocaleString()}</span></div>
          )}
        </div>
      </section>

      <section className="scaffoldBanner">
        <TriangleAlert size={18} />
        <div>
          <strong>설계틀(skeleton) 상태 — 분석 스키마는 정의됨, 내용은 미작성</strong>
          <p>이 프로파일을 채우려면 다음을 실행하세요:</p>
          <code>reddit-report pipeline --config config/{profile.id}.json --allow-fallback</code>
        </div>
      </section>

      {posts.length > 0 && (
        <>
          <section className="metrics" aria-label="summary metrics">
            <Metric icon={<Star size={20} />} label="Top Score" value={numberFmt.format(posts[0]?.score || 0)} />
            <Metric icon={<MessageCircle size={20} />} label="Total Comments" value={numberFmt.format(commentTotal)} />
            <Metric icon={<BarChart3 size={20} />} label="Posts" value={numberFmt.format(posts.length)} />
          </section>

          <TrendingSection trendingPosts={trendingPosts} posts={posts} sortLabel={data?.query?.trending?.sort} />

          <section className="postList" aria-label="collected posts">
            {posts.slice(0, 12).map((post) => (
              <article className="post" key={post.id}>
                <div className="rank">{post.rank}</div>
                <div>
                  <div className="postTopline">
                    <span>r/{post.subredditName}</span>
                    <span>{post.flair || 'Unflaired'}</span>
                  </div>
                  <h2>{post.title}</h2>
                  <div className="postStats">
                    <span>{numberFmt.format(post.score)} score</span>
                    <span>{numberFmt.format(post.comments)} comments</span>
                    <a href={post.reddit_url} target="_blank" rel="noreferrer">Open <ExternalLink size={14} /></a>
                  </div>
                </div>
              </article>
            ))}
          </section>
        </>
      )}
    </>
  );
}

function Report({
  data,
  posts,
  trendingPosts = [],
  analysis,
  filteredPosts,
  flairs,
  query,
  setQuery,
  flair,
  setFlair,
  sort,
  setSort,
  topScore,
  commentTotal,
}) {
  return (
    <>
      <section className="hero">
        <div>
          <p className="eyebrow">Reddit Trend Reporter</p>
          <h1>{analysis?.headline || 'Subreddit weekly trend report'}</h1>
          <p className="summary">{analysis?.summary || 'Collected posts are ready. Run the Claude report step to add narrative analysis.'}</p>
        </div>
        <div className="metaPanel" aria-label="report metadata">
          <div>
            <CalendarClock size={18} />
            <span>{new Date(data.generated_at).toLocaleString()}</span>
          </div>
          <div>
            <RefreshCw size={18} />
            <span>{data.query.sort}/{data.query.time}</span>
          </div>
        </div>
      </section>

      <section className="metrics" aria-label="summary metrics">
        <Metric icon={<Star size={20} />} label="Top Score" value={numberFmt.format(topScore)} />
        <Metric icon={<MessageCircle size={20} />} label="Total Comments" value={numberFmt.format(commentTotal)} />
        <Metric icon={<BarChart3 size={20} />} label="Posts" value={numberFmt.format(posts.length)} />
      </section>

      {analysis && (
        <section className="analysisGrid">
          <Panel title="Top Topics">
            {(analysis.top_topics || []).map((topic) => (
              <article className="topic" key={topic.name}>
                <h3>{topic.name}</h3>
                <p>{topic.why_it_matters}</p>
                <div className="ids">{(topic.evidence_post_ids || []).join(', ')}</div>
              </article>
            ))}
          </Panel>
          <Panel title="Signals">
            <ul className="plainList">
              {(analysis.signals || []).map((signal) => (
                <li key={`${signal.label}-${signal.detail}`}>
                  <strong>{signal.label}</strong>
                  <span>{signal.detail}</span>
                </li>
              ))}
            </ul>
          </Panel>
          <Panel title="Watch Next">
            <ul className="compactList">{(analysis.watch_next || []).map((item) => <li key={item}>{item}</li>)}</ul>
          </Panel>
        </section>
      )}

      {analysis?.community_voice && (
        <section className="voiceSummary">
          <div>
            <p className="eyebrow">Community Voice</p>
            <h2>댓글 기반 정성평가</h2>
            <p>{analysis.community_voice.summary}</p>
          </div>
          <div className={`sentimentPill ${analysis.community_voice.sentiment || 'unclear'}`}>
            {analysis.community_voice.sentiment}
          </div>
        </section>
      )}

      <TrendingSection trendingPosts={trendingPosts} posts={posts} sortLabel={data.query?.trending?.sort} />

      <section className="toolbar" aria-label="post controls">
        <label className="searchBox">
          <Search size={18} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search posts" />
        </label>
        <label className="selectBox">
          <Filter size={18} />
          <select value={flair} onChange={(event) => setFlair(event.target.value)}>
            {flairs.map((item) => (
              <option key={item} value={item}>
                {item === 'all' ? 'All flairs' : item}
              </option>
            ))}
          </select>
        </label>
        <select className="sortSelect" value={sort} onChange={(event) => setSort(event.target.value)}>
          <option value="rank">Sort by Reddit rank</option>
          <option value="score">Sort by score</option>
          <option value="comments">Sort by comments</option>
        </select>
      </section>

      <section className="postList" aria-label="posts">
        {filteredPosts.map((post) => (
          <article className="post" key={post.id}>
            <div className="rank">{post.rank}</div>
            <div>
              <div className="postTopline">
                <span>r/{post.subredditName}</span>
                <span>{post.flair || 'Unflaired'}</span>
                <span>{new Date(post.created_at).toLocaleDateString()}</span>
              </div>
              <h2>{post.title}</h2>
              {post.text && <p>{post.text}</p>}
              {post.discussion?.comments?.length > 0 && (
                <div className="commentPreview">
                  <strong>Top comments collected</strong>
                  {post.discussion.comments.slice(0, 2).map((comment) => (
                    <p key={comment.id}>{comment.body}</p>
                  ))}
                </div>
              )}
              <div className="postStats">
                <span>{numberFmt.format(post.score)} score</span>
                <span>{numberFmt.format(post.comments)} comments</span>
                {post.upvote_ratio && <span>{Math.round(post.upvote_ratio * 100)}% upvoted</span>}
                <a href={post.reddit_url} target="_blank" rel="noreferrer">
                  Open <ExternalLink size={14} />
                </a>
              </div>
            </div>
          </article>
        ))}
      </section>
    </>
  );
}

function Metric({ icon, label, value }) {
  return (
    <div className="metric">
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Panel({ title, children }) {
  return (
    <section className="panel">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

function CodeBlock({ children }) {
  return <pre className="codeBlock"><code>{children}</code></pre>;
}

createRoot(document.getElementById('root')).render(<App />);
