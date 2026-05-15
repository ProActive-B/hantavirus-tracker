import type { APIRoute } from 'astro';
import feedData from '../../data/feed.json';

export const GET: APIRoute = ({ site }) => {
  const items = (feedData.items as any[]).map((it) => `
    <item>
      <title><![CDATA[${it.title}]]></title>
      <link>${it.source_url}</link>
      <guid isPermaLink="false">${it.id}</guid>
      <pubDate>${new Date(it.published).toUTCString()}</pubDate>
      <description><![CDATA[${it.summary}]]></description>
      <source url="${it.source_url}">${it.source}</source>
    </item>`).join('');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Hantavirus Tracker</title>
    <link>${site ?? ''}</link>
    <description>Hantavirus incident reports, normalized across CDC, WHO, ECDC, PAHO, and ProMED.</description>
    <language>en-us</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    ${items}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: { 'Content-Type': 'application/rss+xml; charset=utf-8' },
  });
};
