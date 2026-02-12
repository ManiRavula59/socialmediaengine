import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Container, Grid, Paper, Typography, AppBar, Toolbar,
  Card, CardContent, Tabs, Tab, Box, CircularProgress,
  Alert, AlertTitle, Chip, Divider
} from '@mui/material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js';
import { Bar, Line, Pie } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [overview, setOverview] = useState(null);
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tabValue, setTabValue] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const [overviewRes, crisisRes, trendingRes] = await Promise.all([
        axios.get(`${API_BASE}/overview`),
        axios.get(`${API_BASE}/insights/crisis-detection`).catch(() => ({ 
          data: { 
            insight_type: 'crisis_detection', 
            llm_insight: { 
              selected_insight: 'No crisis detected at this time',
              all_responses: [] 
            } 
          } 
        })),
        axios.get(`${API_BASE}/insights/trending`).catch(() => ({ 
          data: { 
            insight_type: 'trending', 
            llm_insight: { 
              selected_insight: 'No trending topics available',
              all_responses: [] 
            } 
          } 
        }))
      ]);
      
      setOverview(overviewRes.data);
      setInsights([crisisRes.data, trendingRes.data]);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      setError('Failed to load dashboard. Please check if backend is running.');
    }
    setLoading(false);
  };

  // ============ UNIVERSAL SEARCH HANDLER ============
  // BOTH Search Tab AND Model Arena use this!
  const handleUnifiedSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    setError(null);
    try {
      // Always use /api/ask for BOTH tabs
      const res = await axios.get(`${API_BASE}/ask`, {
        params: { q: searchQuery }
      });
      setSearchResults(res.data);
    } catch (error) {
      console.error('Search error:', error);
      setError('Failed to get response. Please try again.');
    }
    setLoading(false);
  };

  if (loading && !overview) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ ml: 2 }}>
          Loading 500,000 tweets...
        </Typography>
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <AppBar position="static" sx={{ mb: 4, bgcolor: '#1976d2' }}>
        <Toolbar>
          <Typography variant="h5" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            🐦 Social Media Insight Engine
          </Typography>
          <Chip 
            label={`${overview?.total_posts?.toLocaleString() || '500K'} Posts Analyzed`}
            sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', fontWeight: 'bold' }}
          />
        </Toolbar>
      </AppBar>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          <AlertTitle>Error</AlertTitle>
          {error}
        </Alert>
      )}

      <Tabs 
        value={tabValue} 
        onChange={(e, v) => setTabValue(v)} 
        sx={{ mb: 3 }}
        variant="fullWidth"
      >
        <Tab label="📊 Overview" />
        <Tab label="🤖 LLM Insights" />
        <Tab label="🔍 Smart Search" />  {/* Renamed to Smart Search */}
        <Tab label="⚖️ Model Arena" />
      </Tabs>

      {/* ============ TAB 1: OVERVIEW ============ */}
      {tabValue === 0 && overview && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card elevation={3} sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  😊 Sentiment Analysis
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Overall sentiment from 500K tweets
                </Typography>
                <Box sx={{ height: 300, mt: 2 }}>
                  <Pie 
                    data={{
                      labels: ['Positive', 'Neutral', 'Negative'],
                      datasets: [{
                        data: [
                          overview.sentiment?.positive || 0,
                          overview.sentiment?.neutral || 0,
                          overview.sentiment?.negative || 0
                        ],
                        backgroundColor: ['#4caf50', '#ff9800', '#f44336'],
                        borderWidth: 0
                      }]
                    }}
                    options={{
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { position: 'bottom' }
                      }
                    }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card elevation={3} sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  📈 Top Trending Hashtags
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Most discussed topics right now
                </Typography>
                <Box sx={{ height: 300, mt: 2 }}>
                  <Bar 
                    data={{
                      labels: (overview.top_hashtags || []).slice(0, 8).map(h => `#${h.tag}`),
                      datasets: [{
                        label: 'Mentions',
                        data: (overview.top_hashtags || []).slice(0, 8).map(h => h.count),
                        backgroundColor: '#2196f3',
                        borderRadius: 4
                      }]
                    }}
                    options={{
                      maintainAspectRatio: false,
                      indexAxis: 'y',
                      plugins: {
                        legend: { display: false }
                      }
                    }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card elevation={3} sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  ⏰ Posts Over Time
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Last 24 hours activity
                </Typography>
                <Box sx={{ height: 300, mt: 2 }}>
                  <Line 
                    data={{
                      labels: (overview.posts_over_time || []).slice(-24).map(p => 
                        new Date(p.time).getHours() + ':00'
                      ),
                      datasets: [{
                        label: 'Tweets per hour',
                        data: (overview.posts_over_time || []).slice(-24).map(p => p.count),
                        borderColor: '#9c27b0',
                        backgroundColor: 'rgba(156, 39, 176, 0.1)',
                        tension: 0.4,
                        fill: true
                      }]
                    }}
                    options={{
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false }
                      }
                    }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* ============ TAB 2: LLM INSIGHTS ============ */}
      {tabValue === 1 && (
        <Grid container spacing={3}>
          {insights.map((insight, i) => (
            <Grid item xs={12} key={i}>
              <Card sx={{ 
                bgcolor: insight.insight_type === 'crisis_detection' ? '#ffebee' : '#e8f5e9',
                borderLeft: 6,
                borderColor: insight.insight_type === 'crisis_detection' ? '#f44336' : '#4caf50',
                mb: 2
              }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {insight.insight_type === 'crisis_detection' ? '🚨 Crisis Detection' : '📈 Trending Topic'}
                    </Typography>
                    {insight.insight_type === 'crisis_detection' && insight.metrics?.spike_percentage && (
                      <Chip 
                        label={`${insight.metrics.spike_percentage} spike`}
                        color="error"
                        size="small"
                        sx={{ ml: 2 }}
                      />
                    )}
                  </Box>
                  
                  {insight.metrics && (
                    <Grid container spacing={2} sx={{ mb: 2 }}>
                      {insight.metrics.negative_tweets !== undefined && (
                        <>
                          <Grid item xs={12} md={3}>
                            <Typography variant="body2" color="text.secondary">Negative Tweets</Typography>
                            <Typography variant="h6">{insight.metrics.negative_tweets}</Typography>
                          </Grid>
                          <Grid item xs={12} md={3}>
                            <Typography variant="body2" color="text.secondary">Spike</Typography>
                            <Typography variant="h6" color="error">{insight.metrics.spike_percentage}</Typography>
                          </Grid>
                          <Grid item xs={12} md={6}>
                            <Typography variant="body2" color="text.secondary">Keywords</Typography>
                            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                              {insight.metrics.keywords?.map((kw, idx) => (
                                <Chip key={idx} label={kw} size="small" variant="outlined" />
                              ))}
                            </Box>
                          </Grid>
                        </>
                      )}
                      {insight.hashtag && (
                        <>
                          <Grid item xs={12} md={3}>
                            <Typography variant="body2" color="text.secondary">Hashtag</Typography>
                            <Typography variant="h6">#{insight.hashtag}</Typography>
                          </Grid>
                          <Grid item xs={12} md={3}>
                            <Typography variant="body2" color="text.secondary">Mentions</Typography>
                            <Typography variant="h6">{insight.mentions}</Typography>
                          </Grid>
                          <Grid item xs={12} md={3}>
                            <Typography variant="body2" color="text.secondary">Positive Sentiment</Typography>
                            <Typography variant="h6" color="success.main">{insight.sentiment?.positive_pct}</Typography>
                          </Grid>
                        </>
                      )}
                    </Grid>
                  )}

                  {insight.llm_insight?.selected_insight && (
                    <Card sx={{ bgcolor: 'rgba(255,255,255,0.7)', p: 2, mb: 2 }}>
                      <Typography variant="body1" sx={{ fontStyle: 'italic' }}>
                        "{insight.llm_insight.selected_insight}"
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                        Generated by: {insight.llm_insight.selected_model} • 
                        Confidence: {insight.llm_insight.confidence}% • 
                        Latency: {insight.llm_insight.latency}s
                      </Typography>
                    </Card>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* ============ TAB 3: SMART SEARCH (FIXED!) ============ */}
      {tabValue === 2 && (
        <Card elevation={3}>
          <CardContent>
            <Typography variant="h5" gutterBottom fontWeight="bold">
              🔍 Smart Search - Understands Any Question
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Ask anything about the 500,000 tweets. I understand both content AND hashtags/trends!
            </Typography>
            
            <form onSubmit={handleUnifiedSearch} style={{ marginBottom: 30 }}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="e.g., What do people think about iPhone? OR top 10 hashtags OR trending today"
                  style={{
                    flex: 1,
                    padding: 12,
                    fontSize: 16,
                    borderRadius: 8,
                    border: '1px solid #ccc',
                    outline: 'none'
                  }}
                />
                <button type="submit" style={{
                  padding: '12px 32px',
                  fontSize: 16,
                  backgroundColor: '#2196f3',
                  color: 'white',
                  border: 'none',
                  borderRadius: 8,
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}>
                  {loading ? <CircularProgress size={24} color="inherit" /> : 'Ask AI'}
                </button>
              </Box>
            </form>

            {searchResults && (
              <Box>
                <Divider sx={{ my: 2 }} />
                
                {/* CONTENT TYPE RESPONSE (sentiment, opinions) */}
                {searchResults.type === 'content' && (
                  <>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h6">
                        📊 Analysis for "{searchResults.question}"
                      </Typography>
                      <Chip 
                        label={`${searchResults.statistics?.total_relevant_tweets || 0} relevant tweets`}
                        color="primary"
                      />
                    </Box>

                    {/* Sentiment Cards */}
                    {searchResults.statistics?.sentiment && (
                      <Grid container spacing={2} sx={{ mb: 3 }}>
                        <Grid item xs={4}>
                          <Card sx={{ bgcolor: '#4caf50', color: 'white', textAlign: 'center', p: 2 }}>
                            <Typography variant="h4">{searchResults.statistics.sentiment.positive}</Typography>
                            <Typography variant="body2">Positive</Typography>
                            <Typography variant="h6">{searchResults.statistics.sentiment.positive_pct}%</Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={4}>
                          <Card sx={{ bgcolor: '#ff9800', color: 'white', textAlign: 'center', p: 2 }}>
                            <Typography variant="h4">{searchResults.statistics.sentiment.neutral}</Typography>
                            <Typography variant="body2">Neutral</Typography>
                            <Typography variant="h6">{searchResults.statistics.sentiment.neutral_pct}%</Typography>
                          </Card>
                        </Grid>
                        <Grid item xs={4}>
                          <Card sx={{ bgcolor: '#f44336', color: 'white', textAlign: 'center', p: 2 }}>
                            <Typography variant="h4">{searchResults.statistics.sentiment.negative}</Typography>
                            <Typography variant="body2">Negative</Typography>
                            <Typography variant="h6">{searchResults.statistics.sentiment.negative_pct}%</Typography>
                          </Card>
                        </Grid>
                      </Grid>
                    )}

                    {/* AI Summary */}
                    {searchResults.answer && (
                      <Card sx={{ bgcolor: '#e3f2fd', p: 3, mb: 3 }}>
                        <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                          🤖 AI Analysis
                        </Typography>
                        <Typography variant="body1" sx={{ fontStyle: 'italic', fontSize: '1.1rem' }}>
                          {searchResults.answer}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                          <Chip label={`Model: ${searchResults.model_used?.split('/')[1]?.split(':')[0] || 'AI'}`} size="small" />
                          <Chip label={`Confidence: ${searchResults.confidence}%`} size="small" color="success" />
                          <Chip label={`${searchResults.statistics?.unique_users || 0} unique users`} size="small" variant="outlined" />
                        </Box>
                      </Card>
                    )}

                    {/* Sample Tweets */}
                    {searchResults.sample_tweets?.length > 0 && (
                      <>
                        <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                          📝 Sample Tweets
                        </Typography>
                        {searchResults.sample_tweets.map((tweet, idx) => (
                          <Card key={idx} sx={{ mb: 1, p: 2, bgcolor: '#fafafa' }}>
                            <Typography variant="body2">{tweet}</Typography>
                          </Card>
                        ))}
                      </>
                    )}
                  </>
                )}

                {/* ANALYTICS TYPE RESPONSE (hashtags, trends) */}
                {searchResults.type === 'analytics' && searchResults.subtype === 'top_hashtags' && (
                  <>
                    <Typography variant="h6" gutterBottom>
                      📊 Top Trending Hashtags
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      Based on {searchResults.data?.length || 0} hashtags from 500K tweets
                    </Typography>

                    {/* Hashtag Table */}
                    <Box sx={{ mb: 3 }}>
                      <Grid container spacing={1} sx={{ 
                        mb: 1, 
                        fontWeight: 'bold', 
                        bgcolor: '#1976d2', 
                        color: 'white', 
                        p: 1.5, 
                        borderRadius: 1 
                      }}>
                        <Grid item xs={1}>Rank</Grid>
                        <Grid item xs={3}>Hashtag</Grid>
                        <Grid item xs={2}>Mentions</Grid>
                        <Grid item xs={2}>Unique Tweets</Grid>
                        <Grid item xs={2}>Positive %</Grid>
                        <Grid item xs={2}>Negative %</Grid>
                      </Grid>
                      
                      {searchResults.data?.slice(0, 10).map((item, idx) => (
                        <Grid container spacing={1} key={idx} sx={{ 
                          py: 1, 
                          borderBottom: '1px solid #eee',
                          bgcolor: idx % 2 ? '#f9f9f9' : 'white',
                          '&:hover': { bgcolor: '#f0f7ff' }
                        }}>
                          <Grid item xs={1}>
                            <Typography fontWeight="bold">#{idx + 1}</Typography>
                          </Grid>
                          <Grid item xs={3}>
                            <Typography fontWeight="bold" color="primary">
                              {item.hashtag}
                            </Typography>
                          </Grid>
                          <Grid item xs={2}>{item.count.toLocaleString()}</Grid>
                          <Grid item xs={2}>{item.unique_tweets.toLocaleString()}</Grid>
                          <Grid item xs={2}>
                            <span style={{ color: '#4caf50', fontWeight: 'bold' }}>
                              {item.sentiment.positive_pct}%
                            </span>
                          </Grid>
                          <Grid item xs={2}>
                            <span style={{ color: '#f44336', fontWeight: 'bold' }}>
                              {item.sentiment.negative_pct}%
                            </span>
                          </Grid>
                        </Grid>
                      ))}
                    </Box>

                    {/* AI Summary for hashtags */}
                    {searchResults.llm_summary?.selected_insight && (
                      <Card sx={{ bgcolor: '#e8f5e9', p: 3, mt: 2 }}>
                        <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                          🤖 Trend Analysis
                        </Typography>
                        <Typography variant="body1" sx={{ fontStyle: 'italic' }}>
                          {searchResults.llm_summary.selected_insight}
                        </Typography>
                      </Card>
                    )}
                  </>
                )}

                {/* DATASET STATISTICS RESPONSE */}
                {searchResults.type === 'analytics' && searchResults.subtype === 'dataset_stats' && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      📈 Dataset Statistics
                    </Typography>
                    <Grid container spacing={3}>
                      <Grid item xs={12} md={3}>
                        <Card sx={{ p: 3, textAlign: 'center', bgcolor: '#e3f2fd' }}>
                          <Typography variant="body2" color="text.secondary">Total Tweets</Typography>
                          <Typography variant="h3" color="primary" fontWeight="bold">
                            {searchResults.data?.total_tweets?.toLocaleString()}
                          </Typography>
                        </Card>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Card sx={{ p: 3, textAlign: 'center', bgcolor: '#f3e5f5' }}>
                          <Typography variant="body2" color="text.secondary">Unique Hashtags</Typography>
                          <Typography variant="h3" color="secondary" fontWeight="bold">
                            {searchResults.data?.unique_hashtags?.toLocaleString()}
                          </Typography>
                        </Card>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Card sx={{ p: 3, textAlign: 'center', bgcolor: '#e8f5e9' }}>
                          <Typography variant="body2" color="text.secondary">Total Hashtags</Typography>
                          <Typography variant="h3" sx={{ color: '#2e7d32' }} fontWeight="bold">
                            {searchResults.data?.total_hashtags?.toLocaleString()}
                          </Typography>
                        </Card>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Card sx={{ p: 3, textAlign: 'center', bgcolor: '#fff3e0' }}>
                          <Typography variant="body2" color="text.secondary">Unique Users</Typography>
                          <Typography variant="h3" sx={{ color: '#ed6c02' }} fontWeight="bold">
                            {searchResults.data?.unique_users?.toLocaleString()}
                          </Typography>
                        </Card>
                      </Grid>
                    </Grid>
                  </Box>
                )}
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* ============ TAB 4: MODEL ARENA ============ */}
      {tabValue === 3 && (
        <Card elevation={3}>
          <CardContent>
            <Typography variant="h5" gutterBottom fontWeight="bold">
              ⚖️ Model Arena - Compare All 4 AI Models
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Ask any question. All 4 models respond simultaneously. Winner (highest confidence) is highlighted in blue.
            </Typography>
            
            <form onSubmit={handleUnifiedSearch} style={{ marginBottom: 30 }}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Ask anything about the 500K tweets..."
                  style={{
                    flex: 1,
                    padding: 12,
                    fontSize: 16,
                    borderRadius: 8,
                    border: '1px solid #ccc',
                    outline: 'none'
                  }}
                />
                <button type="submit" style={{
                  padding: '12px 32px',
                  fontSize: 16,
                  backgroundColor: '#9c27b0',
                  color: 'white',
                  border: 'none',
                  borderRadius: 8,
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}>
                  {loading ? <CircularProgress size={24} color="inherit" /> : 'Ask All Models'}
                </button>
              </Box>
            </form>

            {searchResults?.answer && (
              <>
                {/* Best Answer */}
                <Card sx={{ bgcolor: '#e3f2fd', p: 3, mb: 3, borderRadius: 2 }}>
                  <Typography variant="h6" gutterBottom color="primary" fontWeight="bold">
                    🏆 Best Answer
                  </Typography>
                  <Typography variant="body1" sx={{ fontSize: '1.1rem', mb: 2 }}>
                    {searchResults.answer}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <Chip label={`Model: ${searchResults.model_used?.split('/')[1]?.split(':')[0] || 'AI'}`} color="primary" />
                    <Chip label={`Confidence: ${searchResults.confidence}%`} color="success" />
                    {searchResults.statistics?.total_relevant_tweets && (
                      <Chip label={`${searchResults.statistics.total_relevant_tweets} relevant tweets`} variant="outlined" />
                    )}
                  </Box>
                </Card>

                {/* All 4 Model Responses */}
                <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                  🤖 All 4 Model Responses
                </Typography>
                <Grid container spacing={3}>
                  {searchResults.llm_summary?.all_responses?.map((response, idx) => (
                    <Grid item xs={12} md={6} lg={3} key={idx}>
                      <Card sx={{ 
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        border: response.model === searchResults.model_used ? 3 : 1,
                        borderColor: response.model === searchResults.model_used ? '#2196f3' : '#e0e0e0',
                        boxShadow: response.model === searchResults.model_used ? '0 0 15px rgba(33,150,243,0.2)' : 'none'
                      }}>
                        <CardContent>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                            <Typography variant="h6" sx={{ 
                              color: response.model.includes('nemotron') ? '#76b900' :
                                     response.model.includes('step') ? '#ff6b4a' :
                                     response.model.includes('trinity') ? '#9c27b0' : '#1976d2',
                              fontWeight: 'bold'
                            }}>
                              {response.model.split('/')[1]?.split(':')[0] || 'Model'}
                            </Typography>
                            {response.model === searchResults.model_used && (
                              <Chip label="WINNER" size="small" sx={{ bgcolor: '#2196f3', color: 'white', fontWeight: 'bold' }} />
                            )}
                          </Box>
                          
                          <Typography variant="body2" sx={{ 
                            mt: 1,
                            minHeight: 120,
                            maxHeight: 200,
                            overflow: 'auto',
                            p: 1.5,
                            bgcolor: '#f5f5f5',
                            borderRadius: 1,
                            fontSize: '0.9rem'
                          }}>
                            {response.content || searchResults.answer}
                          </Typography>
                          
                          <Box sx={{ mt: 2, pt: 1, borderTop: 1, borderColor: 'divider' }}>
                            <Typography variant="caption" display="block" sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <span>⚡ Latency: <strong>{response.latency || searchResults.latency}s</strong></span>
                              <span>🎯 Confidence: <strong style={{ 
                                color: (response.confidence || searchResults.confidence) > 80 ? '#4caf50' : '#ff9800' 
                              }}>
                                {response.confidence || searchResults.confidence}%
                              </strong></span>
                            </Typography>
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </Container>
  );
}

export default App;