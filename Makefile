
ifeq (, $(shell which python3 ))
  $(error "PYTHON=$(PYTHON) not found in $(PATH)")
endif


PYTHON_VERSION_MIN=3.6
PYTHON_VERSION=$(shell python3 -c 'import sys; print("%d.%d"% sys.version_info[0:2])' )
PYTHON_VERSION_OK=$(shell python3 -c 'import sys;\
  print(int(float("%d.%d"% sys.version_info[0:2]) >= $(PYTHON_VERSION_MIN)))' )

ifeq ($(PYTHON_VERSION_OK),0)
  $(error "ERROR: need python must  >= $(PYTHON_VERSION_MIN)")
endif

#export PYTHONPATH=/data/PaymentGateway/PG_Withdraw/


start:clean
	@echo "loading service......"
	@nohup python3 -u kline_trader_main.py > all_prints.log 2>&1 &
	@nohup python3 -u order_book_main.py > all_prints.log 2>&1 &
	@sleep 3s
	@echo "kline_trader_main 进程数(包含子进程):"  $$(ps aux | grep '[p]ython3 -u kline_trader_main.py'  | wc -l)
	@echo "order_book_main 进程数(包含子进程):"  $$(ps aux | grep '[p]ython3 -u order_book_main.py'  | wc -l)


#要先杀子进程
stop:
	@kill -9  $$(ps aux | grep '[p]ython3 -u kline_trader_main.py' | awk '{print $$2}')
	@echo "kline_trader_main stoped"
	@kill -9  $$(ps aux | grep '[p]ython3 -u order_book_main.py' | awk '{print $$2}')
	@echo "order_book_main stoped"


clean:
	@rm -rf *.log
	@find -name "*.pyc" -exec rm -f {} \;
	@find -name __pycache__ | xargs rm -rf
	@find -name .cache | xargs rm -rf



