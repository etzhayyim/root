import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';

const httpLink = createHttpLink({
  uri: typeof window !== 'undefined'
    ? (process.env.NEXT_PUBLIC_GRAPHQL_URL || '/api/graphql')
    : (process.env.GRAPHQL_URL || 'http://localhost:8080/api/graphql'),
});

const authLink = setContext((_, { headers }) => {
  // Add any auth headers here if needed
  return {
    headers: {
      ...headers,
    },
  };
});

export const apolloClient = new ApolloClient({
  link: authLink.concat(httpLink),
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: {
      errorPolicy: 'all',
    },
    query: {
      errorPolicy: 'all',
    },
  },
});

