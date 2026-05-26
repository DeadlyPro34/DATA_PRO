export interface DatasetColumn {
    name: string;
    type: string;
}

export interface Dataset {
    id: number;
    uploaded_file: number;
    cleaned_at: string;
    columns: string[];
    parquet_path: string | null;
    quality_score: number;
    rows?: any[];
}

export interface PaginatedResponse<T> {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
}

export class ChartAPI {
    private baseUrl: string;
    private token: string | null;

    constructor(baseUrl: string = '/api/v1', token: string | null = null) {
        this.baseUrl = baseUrl;
        this.token = token;
    }

    private getHeaders(): HeadersInit {
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
        };
        if (this.token) {
            headers['Authorization'] = `Token ${this.token}`;
        }
        // Add CSRF token for Django if not using Token auth
        const csrfToken = this.getCookie('csrftoken');
        if (csrfToken && !this.token) {
            headers['X-CSRFToken'] = csrfToken;
        }
        return headers;
    }

    private getCookie(name: string): string | null {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    public async getDatasets(): Promise<PaginatedResponse<Dataset>> {
        const response = await fetch(`${this.baseUrl}/datasets/`, {
            method: 'GET',
            headers: this.getHeaders(),
        });
        if (!response.ok) {
            throw new Error(`Failed to fetch datasets: ${response.statusText}`);
        }
        return await response.json();
    }

    public async getDataset(id: number): Promise<Dataset> {
        const response = await fetch(`${this.baseUrl}/datasets/${id}/`, {
            method: 'GET',
            headers: this.getHeaders(),
        });
        if (!response.ok) {
            throw new Error(`Failed to fetch dataset: ${response.statusText}`);
        }
        return await response.json();
    }
}
