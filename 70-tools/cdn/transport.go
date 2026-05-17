package cdn

import "net/http"

func init() {
	defaultSender = func(req *http.Request) (*http.Response, error) {
		return http.DefaultClient.Do(req)
	}
}
