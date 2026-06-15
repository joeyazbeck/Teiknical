.PHONY: setup pipeline dashboard clean

setup:
	python -m pip install -r requirements.txt

pipeline:
	python load_data.py
	python initial_analysis.py
	MPLBACKEND=Agg python statistical_analysis.py
	python data_subset_analysis.py

dashboard:
	python load_data.py
	python -m streamlit run dashboard.py

clean:
	rm -f cell_counts.db
	rm -f cell_count_summary.csv
	rm -f part3_responder_data.csv
	rm -f part3_responder_stats.csv
	rm -f part3_summary.txt
	rm -f part3_responder_boxplots.png
	rm -f part4_*.csv
	rm -f filtered_*.csv