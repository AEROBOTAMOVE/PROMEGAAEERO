def main():
    raise SystemExit("ТЕЛЕГРАМ: 401 Unauthorized — токенът е отменен")
if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        raise SystemExit(1)
